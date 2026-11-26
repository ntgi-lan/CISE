"""SQLite persistence and seed-data loading for StudySpace.

The repository opens one short-lived connection per operation. That keeps the
threaded HTTP server safe (SQLite connections are not shareable across threads)
without introducing a connection pool that the assignment does not need.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from .models import Booking, BookingRequest, Room, format_datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings (start);
"""


def load_rooms(path: str | Path) -> list[Room]:
    """Load and validate the seeded room catalogue (FR-01)."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rooms = [
        Room(
            id=str(item["id"]),
            name=str(item["name"]),
            building=str(item["building"]),
            capacity=int(item["capacity"]),
            features=tuple(str(feature) for feature in item.get("features", ())),
        )
        for item in payload["rooms"]
    ]
    if len({room.id for room in rooms}) != len(rooms):
        raise ValueError("Room ids in the seed catalogue must be unique.")
    return rooms


class BookingStorage:
    """A small repository over one SQLite database file."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _to_booking(row: sqlite3.Row) -> Booking:
        return Booking(
            id=int(row["id"]),
            room_id=str(row["room_id"]),
            name=str(row["name"]),
            email=str(row["email"]),
            start=datetime.fromisoformat(str(row["start"])),
            end=datetime.fromisoformat(str(row["end"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    def create(self, request: BookingRequest) -> Booking:
        """Persist a booking and return it with its generated id."""
        created_at = datetime.now().replace(microsecond=0)
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO bookings (room_id, name, email, start, end, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    request.room_id,
                    request.name,
                    request.email,
                    format_datetime(request.start),
                    format_datetime(request.end),
                    format_datetime(created_at),
                ),
            )
            booking_id = int(cursor.lastrowid or 0)
        return Booking(
            id=booking_id,
            room_id=request.room_id,
            name=request.name,
            email=request.email,
            start=request.start,
            end=request.end,
            created_at=created_at,
        )

    def get(self, booking_id: int) -> Booking | None:
        """Return one booking, or None when the id is unknown."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM bookings WHERE id = ?", (booking_id,)
            ).fetchone()
        return self._to_booking(row) if row is not None else None

    def list_for_date(self, day: date) -> list[Booking]:
        """Return every booking that starts on *day*, ordered by start (FR-09)."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM bookings WHERE start LIKE ? ORDER BY start, id",
                (f"{day.isoformat()}%",),
            ).fetchall()
        return [self._to_booking(row) for row in rows]

    def list_all(self, limit: int = 500) -> list[Booking]:
        """Return recent bookings across every date, ordered by start (FR-09)."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM bookings ORDER BY start, id LIMIT ?", (limit,)
            ).fetchall()
        return [self._to_booking(row) for row in rows]

    def delete(self, booking_id: int) -> bool:
        """Delete a booking; return False when it does not exist (FR-08)."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM bookings WHERE id = ?", (booking_id,)
            )
            deleted = cursor.rowcount > 0
        return deleted


def load_extra_rooms(path: str | Path) -> list[Room]:
    """Load rooms added through the API; they live beside the seed file."""
    location = Path(path)
    if not location.exists():
        return []
    payload = json.loads(location.read_text(encoding="utf-8"))
    rooms = []
    for row in payload.get("rooms", []):
        rooms.append(
            Room(
                id=str(row["id"]),
                name=str(row["name"]),
                building=str(row["building"]),
                capacity=int(row["capacity"]),
                features=tuple(str(feature) for feature in row.get("features", [])),
            )
        )
    return rooms


def append_extra_room(path: str | Path, room: Room) -> None:
    """Persist one added room without touching the seeded catalogue."""
    location = Path(path)
    location.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rooms": []}
    if location.exists():
        payload = json.loads(location.read_text(encoding="utf-8"))
        payload.setdefault("rooms", [])
    payload["rooms"].append(room.to_dict())
    temporary = location.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(location)
