"""Domain models for StudySpace.

The models are immutable dataclasses: a booking cannot be changed while the rule
engine is validating it, and the repository always returns a fresh object. All
datetimes are naive local-time values, which is sufficient for the single-campus
scope of this release.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


def format_datetime(moment: datetime) -> str:
    """Render a datetime as an ISO-8601 string with second precision."""
    return moment.replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class Room:
    """A bookable room from the seeded catalogue (FR-01)."""

    id: str
    name: str
    building: str
    capacity: int
    features: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return the JSON representation used by the HTTP API."""
        return {
            "id": self.id,
            "name": self.name,
            "building": self.building,
            "capacity": self.capacity,
            "features": list(self.features),
        }


@dataclass(frozen=True, slots=True)
class BookingRequest:
    """A booking request whose values have been parsed but not yet validated."""

    room_id: str
    name: str
    email: str
    start: datetime
    end: datetime

    @property
    def day(self) -> date:
        """The calendar date the booking starts on."""
        return self.start.date()


@dataclass(frozen=True, slots=True)
class Booking:
    """A persisted booking (FR-03, FR-08, FR-09)."""

    id: int
    room_id: str
    name: str
    email: str
    start: datetime
    end: datetime
    created_at: datetime

    @property
    def day(self) -> date:
        """The calendar date the booking starts on."""
        return self.start.date()

    def to_dict(self) -> dict[str, object]:
        """Return the JSON representation used by the HTTP API."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "name": self.name,
            "email": self.email,
            "start": format_datetime(self.start),
            "end": format_datetime(self.end),
            "created_at": format_datetime(self.created_at),
        }
