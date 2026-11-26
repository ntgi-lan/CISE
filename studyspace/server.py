"""HTTP layer for StudySpace: routing, validation and error mapping.

``ThreadingHTTPServer`` serves the JSON API under ``/api/`` and the static
single-page front-end from ``studyspace/web/``. Validation errors are raised as
:class:`~studyspace.rules.RuleViolation` and translated into the JSON error
contract ``{"error": {"code": ..., "message": ...}}``.
"""

from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .models import BookingRequest, format_datetime, Room
from .rules import (
    find_overlap,
    next_free_window,
    RuleViolation,
    check_daily_limit,
    check_overlap,
    rooms_free_for_window,
    validate_booking,
    validate_search,
)
from .storage import (
    BookingStorage,
    append_extra_room,
    load_extra_rooms,
    load_rooms,
)

WEB_DIR = Path(__file__).with_name("web")
MAX_BODY_BYTES = 64 * 1024
BOOKING_FIELDS = ("room_id", "name", "email", "start", "end")


class StudySpaceServer(ThreadingHTTPServer):
    """Threading HTTP server carrying the application dependencies."""

    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        storage: BookingStorage,
        rooms: list[Room],
        clock: Callable[[], datetime],
        rooms_extra_path: str | Path = "data/rooms_added.json",
    ) -> None:
        super().__init__(address, StudySpaceHandler)
        self.storage = storage
        self.rooms = rooms
        self.rooms_extra_path = rooms_extra_path
        self.rooms_by_id = {room.id: room for room in rooms}
        self.clock = clock


class StudySpaceHandler(BaseHTTPRequestHandler):
    """Request handler for the JSON API and the static front-end."""

    server: StudySpaceServer
    protocol_version = "HTTP/1.1"
    server_version = f"StudySpace/{__version__}"

    # -- request entry points ------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def log_message(self, format: str, *args: object) -> None:
        """Stay quiet under unittest; a deployment would use the logging module."""
        return

    # -- routing -------------------------------------------------------------

    def _dispatch(self, method: str) -> None:
        try:
            parsed = urlsplit(self.path)
            if parsed.path.startswith("/api/"):
                self._handle_api(method, parsed.path, parse_qs(parsed.query))
            elif method == "GET":
                self._serve_static(parsed.path)
            else:
                self._send_error(404, "not_found", "Unknown endpoint.")
        except RuleViolation as violation:
            self._send_error(
                violation.status, violation.code, violation.message, violation.details
            )
        except Exception as error:  # pragma: no cover - defensive last resort
            self._send_error(500, "internal_error", f"Unexpected server error: {error}")

    def _handle_api(
        self, method: str, path: str, query: dict[str, list[str]]
    ) -> None:
        if path == "/api/health" and method == "GET":
            self._send_json(200, {"status": "ok", "version": __version__})
            return
        if path == "/api/rooms":
            if method == "GET":
                self._send_json(200, self._rooms_payload(query))
                return
            if method == "POST":
                self._create_room()
                return
        if path == "/api/bookings":
            if method == "GET":
                self._send_json(200, self._bookings_payload(query))
                return
            if method == "POST":
                self._create_booking()
                return
        if path == "/api/waitlist":
            if method == "GET":
                self._send_json(200, self._waitlist_payload(query))
                return
            if method == "POST":
                self._create_waitlist()
                return
        if path.startswith("/api/bookings/") and method == "DELETE":
            self._delete_booking(path.rsplit("/", 1)[-1])
            return
        if path in {"/api/health", "/api/rooms", "/api/bookings"}:
            self._send_error(
                405, "method_not_allowed", f"{method} is not supported for {path}."
            )
            return
        self._send_error(404, "not_found", f"Unknown endpoint: {path}")

    # -- room catalogue and search (FR-01, FR-02) ----------------------------

    def _rooms_payload(self, query: dict[str, list[str]]) -> dict[str, object]:
        building_values = query.get("building")
        building = building_values[0].strip().upper() if building_values else None
        if not building:
            building = None
        has_search = any(
            key in query for key in ("start", "end", "min_capacity")
        )
        if not has_search:
            rooms = list(self.server.rooms)
            if building:
                rooms = [room for room in rooms if room.building.upper() == building]
            return {"rooms": [room.to_dict() for room in rooms], "count": len(rooms)}

        start = self._query_datetime(query, "start")
        end = self._query_datetime(query, "end")
        min_capacity = self._query_int(query, "min_capacity")
        validate_search(start, end, min_capacity)
        bookings = self.server.storage.list_for_date(start.date())
        free_rooms = rooms_free_for_window(
            self.server.rooms, bookings, start, end, min_capacity
        )
        if building:
            free_rooms = [room for room in free_rooms if room.building.upper() == building]
        return {
            "rooms": [room.to_dict() for room in free_rooms],
            "count": len(free_rooms),
        }

    def _create_room(self) -> None:
        payload = self._read_json_object()
        room = self._parse_room(payload)
        if room.id in self.server.rooms_by_id:
            raise RuleViolation(
                "room_exists", f"Room '{room.id}' already exists.", status=409
            )
        append_extra_room(self.server.rooms_extra_path, room)
        self.server.rooms.append(room)
        self.server.rooms_by_id[room.id] = room
        self._send_json(
            201, room.to_dict(), headers={"Location": f"/api/rooms/{room.id}"}
        )

    def _parse_room(self, payload: dict[str, object]) -> Room:
        identifier = str(payload.get("id", "")).strip().upper()
        name = str(payload.get("name", "")).strip()
        building = str(payload.get("building", "")).strip().upper()
        capacity_raw = payload.get("capacity", 0)
        features_raw = payload.get("features", [])
        if not identifier or not all(
            part for part in [identifier.replace("-", "").replace(" ", "")]
        ):
            raise RuleViolation(
                "invalid_room", "Room id is required, for example WA-301."
            )
        if not name:
            raise RuleViolation("invalid_room", "Room name is required.")
        if not building:
            raise RuleViolation("invalid_room", "Building is required.")
        try:
            capacity = int(capacity_raw)
        except (TypeError, ValueError) as error:
            raise RuleViolation(
                "invalid_room", "Capacity must be a whole number."
            ) from error
        if capacity < 1 or capacity > 50:
            raise RuleViolation(
                "invalid_room", "Capacity must be between 1 and 50."
            )
        if not isinstance(features_raw, list) or not all(
            isinstance(feature, str) for feature in features_raw
        ):
            raise RuleViolation(
                "invalid_room", "Features must be a list of strings."
            )
        return Room(
            id=identifier,
            name=name,
            building=building,
            capacity=capacity,
            features=tuple(feature.strip() for feature in features_raw if feature.strip()),
        )

    # -- bookings (FR-03 to FR-09) -------------------------------------------

    def _bookings_payload(self, query: dict[str, list[str]]) -> dict[str, object]:
        if query.get("all", [""])[0] == "1":
            bookings = self.server.storage.list_all()
            return {
                "bookings": [booking.to_dict() for booking in bookings],
                "count": len(bookings),
            }
        values = query.get("date")
        if values:
            try:
                day = date.fromisoformat(values[0])
            except ValueError as error:
                raise RuleViolation(
                    "invalid_query",
                    "Query parameter 'date' must use the form YYYY-MM-DD.",
                ) from error
        else:
            day = self.server.clock().date()
        bookings = self.server.storage.list_for_date(day)
        return {
            "date": day.isoformat(),
            "bookings": [booking.to_dict() for booking in bookings],
            "count": len(bookings),
        }

    def _alternatives(self, request, conflict, day_bookings):
        """Suggest the next free window in this room and other free rooms (FR-11)."""
        duration = request.end - request.start
        following = next_free_window(
            request.room_id, request.day, request.end, duration, day_bookings
        )
        free_rooms = rooms_free_for_window(
            self.server.rooms, day_bookings, request.start, request.end, 0
        )
        others = [room for room in free_rooms if room.id != request.room_id][:3]
        return {
            "conflict": {
                "room_id": conflict.room_id,
                "start": format_datetime(conflict.start),
                "end": format_datetime(conflict.end),
            },
            "next_free": (
                {
                    "room_id": request.room_id,
                    "start": format_datetime(following[0]),
                    "end": format_datetime(following[1]),
                }
                if following
                else None
            ),
            "other_rooms": [
                {
                    "room_id": room.id,
                    "name": room.name,
                    "start": format_datetime(request.start),
                    "end": format_datetime(request.end),
                }
                for room in others
            ],
        }

    def _create_waitlist(self) -> None:
        payload = self._read_json_object()
        request = self._parse_booking_request(payload)
        if request.room_id not in self.server.rooms_by_id:
            raise RuleViolation(
                "room_not_found",
                f"Room '{request.room_id}' does not exist.",
                status=404,
            )
        now = self.server.clock()
        validate_booking(request, now)
        day_bookings = self.server.storage.list_for_date(request.start.date())
        if find_overlap(request.room_id, request.start, request.end, day_bookings) is None:
            raise RuleViolation(
                "room_free",
                "The room is free for that window; book it directly.",
                status=400,
            )
        existing = self.server.storage.find_waitlist_by_email(
            request.room_id, request.email, request.start
        )
        if existing is not None:
            raise RuleViolation(
                "already_waiting",
                "You are already on the waitlist for that slot.",
                status=409,
            )
        entry_id, position = self.server.storage.add_waitlist(
            request.room_id, request.name, request.email, request.start, request.end
        )
        self._send_json(
            201,
            {
                "id": entry_id,
                "position": position,
                "room_id": request.room_id,
                "start": format_datetime(request.start),
                "end": format_datetime(request.end),
                "message": "You will be booked automatically if the slot is cancelled.",
            },
            headers={"Location": f"/api/waitlist/{entry_id}"},
        )

    def _waitlist_payload(self, query: dict[str, list[str]]) -> dict[str, object]:
        values = query.get("date")
        day = None
        if values:
            try:
                day = date.fromisoformat(values[0])
            except ValueError as error:
                raise RuleViolation(
                    "invalid_query",
                    "Query parameter 'date' must use the form YYYY-MM-DD.",
                ) from error
        entries = self.server.storage.list_waitlist(day)
        return {"entries": entries, "count": len(entries)}

    def _promote_waitlist(self, booking) -> object | None:
        now = self.server.clock()
        for entry in self.server.storage.waitlist_for_room_day(
            booking.room_id, booking.start.date()
        ):
            start = datetime.fromisoformat(str(entry["start"]))
            end = datetime.fromisoformat(str(entry["end"]))
            if start < now:
                self.server.storage.remove_waitlist(int(entry["id"]))
                continue
            day_bookings = self.server.storage.list_for_date(start.date())
            if find_overlap(booking.room_id, start, end, day_bookings) is not None:
                continue
            promoted = self.server.storage.create(
                BookingRequest(
                    room_id=booking.room_id,
                    name=str(entry["name"]),
                    email=str(entry["email"]),
                    start=start,
                    end=end,
                )
            )
            self.server.storage.remove_waitlist(int(entry["id"]))
            return promoted
        return None

    def _create_booking(self) -> None:
        payload = self._read_json_object()
        request = self._parse_booking_request(payload)
        if request.room_id not in self.server.rooms_by_id:
            raise RuleViolation(
                "room_not_found",
                f"Room '{request.room_id}' does not exist.",
                status=404,
            )

        now = self.server.clock()
        validate_booking(request, now)
        day_bookings = self.server.storage.list_for_date(request.start.date())
        check_daily_limit(request.email, request.start.date(), day_bookings, now)
# FR-03: the same room cannot be booked over an existing booking. The interval is
        # half-open, so a booking that ends at 11:00 and one that starts at 11:00 do not
        # overlap. This runs after the daily-limit check and before persistence, so a
        # refused request creates no record.
        conflict = find_overlap(request.room_id, request.start, request.end, day_bookings)
        if conflict is not None:
            raise RuleViolation(
                "overlap",
                f"Room {request.room_id} is already booked from "
                f"{conflict.start:%H:%M} to {conflict.end:%H:%M} on "
                f"{conflict.start.date().isoformat()}.",
                status=409,
                details=self._alternatives(request, conflict, day_bookings),
            )

        booking = self.server.storage.create(request)
        self._send_json(
            201,
            booking.to_dict(),
            headers={"Location": f"/api/bookings/{booking.id}"},
        )

    def _delete_booking(self, identifier: str) -> None:
        try:
            booking_id = int(identifier)
        except ValueError as error:
            raise RuleViolation(
                "invalid_request", "Booking id must be an integer."
            ) from error
        booking = self.server.storage.get(booking_id)
        if booking is None or not self.server.storage.delete(booking_id):
            raise RuleViolation(
                "booking_not_found",
                f"Booking {booking_id} does not exist.",
                status=404,
            )
        promoted = self._promote_waitlist(booking)
        if promoted is not None:
            self._send_json(
                200,
                {
                    "promoted": promoted.to_dict(),
                    "message": "The cancelled slot was given to the first person on the waitlist.",
                },
            )
            return
        self._send_json(204, None)

    # -- request parsing helpers --------------------------------------------

    def _read_json_object(self) -> dict[str, object]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise RuleViolation(
                "invalid_json", "A JSON request body is required.", status=422
            )
        try:
            length = int(raw_length)
        except ValueError as error:
            raise RuleViolation(
                "invalid_json", "Content-Length must be an integer.", status=422
            ) from error
        if length <= 0:
            raise RuleViolation(
                "invalid_json", "A JSON request body is required.", status=422
            )
        if length > MAX_BODY_BYTES:
            raise RuleViolation(
                "payload_too_large", "Request body is too large.", status=422
            )
        try:
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError) as error:
            raise RuleViolation(
                "invalid_json", "Request body must be valid JSON.", status=422
            ) from error
        if not isinstance(payload, dict):
            raise RuleViolation(
                "invalid_json", "Request body must be a JSON object.", status=422
            )
        return payload

    def _parse_booking_request(self, payload: dict[str, object]) -> BookingRequest:
        missing = [field for field in BOOKING_FIELDS if field not in payload]
        if missing:
            raise RuleViolation(
                "invalid_request",
                f"Missing required field(s): {', '.join(missing)}.",
                status=422,
            )
        for field in ("room_id", "name", "email"):
            if not isinstance(payload[field], str):
                raise RuleViolation(
                    "invalid_request", f"Field '{field}' must be a string.", status=422
                )
        return BookingRequest(
            room_id=str(payload["room_id"]).strip(),
            name=str(payload["name"]),
            email=str(payload["email"]).strip(),
            start=self._parse_datetime_field(payload, "start"),
            end=self._parse_datetime_field(payload, "end"),
        )

    @staticmethod
    def _parse_datetime_field(payload: dict[str, object], field: str) -> datetime:
        value = payload[field]
        if not isinstance(value, str):
            raise RuleViolation(
                "invalid_datetime", f"Field '{field}' must be an ISO-8601 string."
            )
        try:
            return datetime.fromisoformat(value)
        except ValueError as error:
            raise RuleViolation(
                "invalid_datetime",
                f"Field '{field}' must be an ISO-8601 date-time, "
                "for example 2026-11-05T10:00:00.",
            ) from error

    @staticmethod
    def _query_datetime(query: dict[str, list[str]], name: str) -> datetime:
        values = query.get(name)
        if not values:
            raise RuleViolation(
                "invalid_query", f"Query parameter '{name}' is required."
            )
        try:
            return datetime.fromisoformat(values[0])
        except ValueError as error:
            raise RuleViolation(
                "invalid_datetime",
                f"Query parameter '{name}' must be an ISO-8601 date-time.",
            ) from error

    @staticmethod
    def _query_int(
        query: dict[str, list[str]], name: str
    ) -> int | None:
        values = query.get(name)
        if not values:
            return None
        try:
            return int(values[0])
        except ValueError as error:
            raise RuleViolation(
                "invalid_query", f"Query parameter '{name}' must be an integer."
            ) from error

    # -- static files (web/) -------------------------------------------------

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        web_root = WEB_DIR.resolve()
        candidate = (WEB_DIR / relative).resolve()
        if candidate != web_root and web_root not in candidate.parents:
            self._send_error(404, "not_found", "File not found.")
            return
        if not candidate.is_file():
            self._send_error(404, "not_found", "File not found.")
            return
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type = f"{content_type}; charset=utf-8"
        body = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- response helpers ----------------------------------------------------

    def _send_json(
        self,
        status: int,
        payload: dict[str, object] | None,
        headers: dict[str, str] | None = None,
    ) -> None:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_error(
        self,
        status: int,
        code: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        error: dict[str, object] = {"code": code, "message": message}
        if details is not None:
            error["details"] = details
        self._send_json(status, {"error": error})


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    db_path: str | Path = "data/studyspace.db",
    rooms_path: str | Path = "data/rooms.json",
    clock: Callable[[], datetime] | None = None,
    rooms_extra_path: str | Path | None = None,
) -> StudySpaceServer:
    """Build a configured server.

    Passing ``port=0`` asks the operating system for an ephemeral port, which the
    integration tests use. The clock is injectable so tests can pin "now".
    """
    storage = BookingStorage(db_path)
    rooms = load_rooms(rooms_path)
    extra_path = (
        Path(rooms_extra_path)
        if rooms_extra_path is not None
        else Path(rooms_path).with_name("rooms_added.json")
    )
    known = {room.id for room in rooms}
    for room in load_extra_rooms(extra_path):
        if room.id not in known:
            rooms.append(room)
            known.add(room.id)
    return StudySpaceServer(
        (host, port), storage, rooms, clock or datetime.now, extra_path
    )
