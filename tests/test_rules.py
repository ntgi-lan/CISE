"""Unit tests for the booking rule engine (NFR-01, NFR-04).

The rules are pure functions, so these tests need no server and no database.
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta

from studyspace import rules
from studyspace.models import Booking, BookingRequest

NOW = datetime(2026, 11, 4, 8, 0)  # Wednesday, before opening
WEDNESDAY = datetime(2026, 11, 4, 10, 0)
SATURDAY = datetime(2026, 11, 7, 10, 0)


def make_request(
    start: datetime,
    end: datetime,
    *,
    name: str = "Alex Student",
    email: str = "alex.student@autuni.ac.nz",
    room_id: str = "WA-201",
) -> BookingRequest:
    """Build a booking request for the rule under test."""
    return BookingRequest(room_id=room_id, name=name, email=email, start=start, end=end)


def make_booking(start: datetime, *, email: str = "alex.student@autuni.ac.nz") -> Booking:
    """Build a stored booking without touching the database."""
    return Booking(
        id=1,
        room_id="WA-201",
        name="Alex Student",
        email=email,
        start=start,
        end=start + timedelta(hours=1),
        created_at=NOW,
    )


class OpeningHoursTests(unittest.TestCase):
    """FR-04: opening hours are 07:00-22:00 weekdays and 09:00-18:00 weekends."""

    def test_weekday_booking_inside_opening_hours_is_allowed(self) -> None:
        request = make_request(WEDNESDAY, WEDNESDAY + timedelta(hours=1))
        rules.validate_booking(request, NOW)  # must not raise

    def test_weekday_booking_before_opening_is_rejected(self) -> None:
        request = make_request(
            WEDNESDAY.replace(hour=6, minute=30),
            WEDNESDAY.replace(hour=7, minute=30),
        )
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "opening_hours")
        self.assertEqual(raised.exception.status, 400)

    def test_weekday_booking_after_closing_is_rejected(self) -> None:
        request = make_request(
            WEDNESDAY.replace(hour=21, minute=45),
            WEDNESDAY.replace(hour=22, minute=30),
        )
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "opening_hours")

    def test_weekend_opening_hours_are_enforced(self) -> None:
        too_early = make_request(
            SATURDAY.replace(hour=8, minute=0),
            SATURDAY.replace(hour=9, minute=0),
        )
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(too_early, NOW)
        self.assertEqual(raised.exception.code, "opening_hours")

        valid = make_request(
            SATURDAY.replace(hour=9, minute=0),
            SATURDAY.replace(hour=10, minute=0),
        )
        rules.validate_booking(valid, NOW)  # must not raise


class SlotAndDurationTests(unittest.TestCase):
    """FR-04 slot boundaries and FR-05 duration limits."""

    def test_unaligned_slot_boundary_is_rejected(self) -> None:
        request = make_request(
            WEDNESDAY.replace(minute=7),
            WEDNESDAY.replace(minute=7) + timedelta(hours=1),
        )
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "slot_alignment")

    def test_duration_shorter_than_thirty_minutes_is_rejected(self) -> None:
        request = make_request(WEDNESDAY, WEDNESDAY + timedelta(minutes=15))
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "duration")

    def test_duration_longer_than_two_hours_is_rejected(self) -> None:
        request = make_request(WEDNESDAY, WEDNESDAY + timedelta(minutes=150))
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "duration")

    def test_duration_boundaries_of_thirty_and_one_hundred_and_twenty_are_allowed(self) -> None:
        for minutes in (30, 120):
            with self.subTest(minutes=minutes):
                start = WEDNESDAY.replace(hour=10, minute=0)
                request = make_request(start, start + timedelta(minutes=minutes))
                rules.validate_booking(request, NOW)  # must not raise


class PastBookingTests(unittest.TestCase):
    """FR-06: bookings cannot start before the current local time."""

    def test_booking_in_the_past_is_rejected(self) -> None:
        yesterday = datetime(2026, 11, 3, 10, 0)
        request = make_request(yesterday, yesterday + timedelta(hours=1))
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.validate_booking(request, NOW)
        self.assertEqual(raised.exception.code, "past_booking")


class DailyLimitTests(unittest.TestCase):
    """FR-07: at most two future bookings per email per day."""

    def test_third_future_booking_for_the_same_email_is_rejected(self) -> None:
        day = date(2026, 11, 5)
        first_two = [
            make_booking(datetime(2026, 11, 5, 10, 0)),
            make_booking(datetime(2026, 11, 5, 11, 0)),
        ]
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.check_daily_limit("alex.student@autuni.ac.nz", day, first_two, NOW)
        self.assertEqual(raised.exception.code, "daily_limit")
        self.assertEqual(raised.exception.status, 409)

        # The limit is not hit until the second future booking already exists.
        rules.check_daily_limit(
            "alex.student@autuni.ac.nz", day, first_two[:1], NOW
        )  # must not raise


class OverlapTests(unittest.TestCase):
    """FR-03: a room cannot be booked twice for overlapping windows."""

    def test_overlapping_booking_for_the_same_room_is_rejected(self) -> None:
        existing = [make_booking(datetime(2026, 11, 5, 10, 0))]
        request = make_request(
            datetime(2026, 11, 5, 10, 30), datetime(2026, 11, 5, 11, 30)
        )
        with self.assertRaises(rules.RuleViolation) as raised:
            rules.check_overlap(request.room_id, request.start, request.end, existing)
        self.assertEqual(raised.exception.code, "overlap")
        self.assertEqual(raised.exception.status, 409)

    def test_adjacent_slots_and_other_rooms_do_not_overlap(self) -> None:
        existing = [make_booking(datetime(2026, 11, 5, 10, 0))]

        # 11:00-12:00 starts exactly when the existing booking ends.
        adjacent = make_request(
            datetime(2026, 11, 5, 11, 0), datetime(2026, 11, 5, 12, 0)
        )
        rules.check_overlap(
            adjacent.room_id, adjacent.start, adjacent.end, existing
        )  # must not raise

        # A different room is unaffected by the existing booking.
        rules.check_overlap(
            "WA-204", adjacent.start, adjacent.end, existing
        )  # must not raise

    def test_overlap_check_has_no_side_effect(self) -> None:
        existing = [make_booking(datetime(2026, 11, 5, 10, 0))]
        snapshot = list(existing)
        request = make_request(
            datetime(2026, 11, 5, 10, 30), datetime(2026, 11, 5, 11, 30)
        )
        with self.assertRaises(rules.RuleViolation):
            rules.check_overlap(request.room_id, request.start, request.end, existing)
        self.assertEqual(existing, snapshot)
        self.assertEqual(len(existing), 1)


if __name__ == "__main__":
    unittest.main()

