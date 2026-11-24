"""Booking rules for StudySpace.

The rules are pure functions with no I/O, so they can be unit-tested directly and
changed without touching the HTTP layer (NFR-04). A broken rule raises
:class:`RuleViolation`, which carries a stable machine-readable ``code`` and the
HTTP status the API layer must return (400 for invalid input, 409 for a
conflict).

Runtime rules (SPEC section 3): Mon-Fri 07:00-22:00, Sat-Sun 09:00-18:00,
15-minute slot boundaries, 30-120 minute duration, overlap rejected, no past
bookings, and at most two future bookings per email per date.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time

from .models import Booking, BookingRequest, Room

SLOT_MINUTES = 15
MIN_DURATION_MINUTES = 30
MAX_DURATION_MINUTES = 120
MAX_FUTURE_BOOKINGS_PER_EMAIL_PER_DAY = 2

WEEKDAY_OPEN = time(7, 0)
WEEKDAY_CLOSE = time(22, 0)
WEEKEND_OPEN = time(9, 0)
WEEKEND_CLOSE = time(18, 0)


class RuleViolation(Exception):
    """A request that breaks a booking or input-validation rule."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status

    def to_dict(self) -> dict[str, object]:
        """Return the JSON error envelope for this violation."""
        return {"error": {"code": self.code, "message": self.message}}


def open_hours_for(day: date) -> tuple[time, time]:
    """Return the opening and closing time for *day* (FR-04)."""
    if day.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return WEEKEND_OPEN, WEEKEND_CLOSE
    return WEEKDAY_OPEN, WEEKDAY_CLOSE


def validate_attendee(name: str, email: str) -> None:
    """Reject empty or obviously malformed attendee details."""
    if not name.strip():
        raise RuleViolation("invalid_attendee", "A booking name is required.")
    normalised = email.strip()
    domain = normalised.rsplit("@", 1)[-1] if "@" in normalised else ""
    if not domain or "." not in domain:
        raise RuleViolation("invalid_attendee", "A valid email address is required.")


def validate_duration(start: datetime, end: datetime) -> None:
    """Enforce the 30-120 minute duration window (FR-05)."""
    minutes = (end - start).total_seconds() / 60
    if minutes < MIN_DURATION_MINUTES or minutes > MAX_DURATION_MINUTES:
        raise RuleViolation(
            "duration",
            f"Bookings must last between {MIN_DURATION_MINUTES} and "
            f"{MAX_DURATION_MINUTES} minutes.",
        )


def validate_slot_alignment(start: datetime, end: datetime) -> None:
    """Enforce 15-minute slot boundaries (FR-04)."""
    for moment in (start, end):
        if moment.minute % SLOT_MINUTES or moment.second or moment.microsecond:
            raise RuleViolation(
                "slot_alignment",
                f"Bookings must start and end on a {SLOT_MINUTES}-minute boundary.",
            )


def validate_opening_hours(start: datetime, end: datetime) -> None:
    """Enforce the opening hours of the start day (FR-04)."""
    if end.date() != start.date():
        raise RuleViolation(
            "opening_hours", "A booking must start and end on the same day."
        )
    opens, closes = open_hours_for(start.date())
    if start.time() < opens or end.time() > closes:
        raise RuleViolation(
            "opening_hours",
            f"Bookings on {start.date().isoformat()} must be between "
            f"{opens:%H:%M} and {closes:%H:%M}.",
        )


def validate_not_in_past(start: datetime, now: datetime) -> None:
    """Reject bookings that would begin before *now* (FR-06)."""
    if start < now:
        raise RuleViolation("past_booking", "A booking cannot start in the past.")


def validate_booking(request: BookingRequest, now: datetime) -> None:
    """Run the request-shape rules before storage and availability checks."""
    validate_attendee(request.name, request.email)
    validate_duration(request.start, request.end)
    validate_slot_alignment(request.start, request.end)
    validate_opening_hours(request.start, request.end)
    validate_not_in_past(request.start, now)


def validate_search(
    start: datetime, end: datetime, min_capacity: int | None
) -> None:
    """Validate a room-search window and capacity filter (FR-02)."""
    if end <= start:
        raise RuleViolation(
            "invalid_search", "The search window must end after it starts."
        )
    if min_capacity is not None and (min_capacity < 1 or min_capacity > 100):
        raise RuleViolation(
            "invalid_search", "min_capacity must be between 1 and 100."
        )


def check_daily_limit(
    email: str, day: date, bookings: Iterable[Booking], now: datetime
) -> None:
    """Limit each email to two future bookings per day (FR-07)."""
    normalised = email.strip().lower()
    future_count = sum(
        1
        for booking in bookings
        if booking.email.strip().lower() == normalised
        and booking.start.date() == day
        and booking.start >= now
    )
    if future_count >= MAX_FUTURE_BOOKINGS_PER_EMAIL_PER_DAY:
        raise RuleViolation(
            "daily_limit",
            "An email address may hold at most "
            f"{MAX_FUTURE_BOOKINGS_PER_EMAIL_PER_DAY} future bookings per day.",
            status=409,
        )


def overlaps(
    start: datetime, end: datetime, other_start: datetime, other_end: datetime
) -> bool:
    """Return True when the two half-open time windows intersect."""
    return start < other_end and other_start < end


def check_overlap(
    room_id: str, start: datetime, end: datetime, bookings: Iterable[Booking]
) -> None:
    """Reject a booking that intersects an existing booking for the same room (FR-03).

    Adjacent windows do not overlap: a booking that ends at 11:00 and one that
    starts at 11:00 can share the same room. The check is read-only; the caller
    persists the booking only after every rule has passed.
    """
    for booking in bookings:
        if booking.room_id == room_id and overlaps(
            start, end, booking.start, booking.end
        ):
            raise RuleViolation(
                "overlap",
                f"Room {room_id} is already booked from "
                f"{booking.start:%H:%M} to {booking.end:%H:%M} on "
                f"{booking.start.date().isoformat()}.",
                status=409,
            )


def rooms_free_for_window(
    rooms: Iterable[Room],
    bookings: Iterable[Booking],
    start: datetime,
    end: datetime,
    min_capacity: int | None = None,
) -> list[Room]:
    """Return rooms with enough capacity and no overlapping booking (FR-02)."""
    candidates = [
        room
        for room in rooms
        if min_capacity is None or room.capacity >= min_capacity
    ]
    busy_room_ids = {
        booking.room_id
        for booking in bookings
        if overlaps(start, end, booking.start, booking.end)
    }
    return sorted(
        (room for room in candidates if room.id not in busy_room_ids),
        key=lambda room: (room.building, room.id),
    )
