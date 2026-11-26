"""Integration tests for the StudySpace JSON API (FR-01 to FR-10, NFR-01).

Every test starts the real server on an ephemeral port with a temporary SQLite
database and talks to it over HTTP with urllib. The server clock is pinned by the
test fixture, so the dates below are deterministic.
"""

from __future__ import annotations

import unittest

from helpers import BOOKING_DAY, ServerTestCase, booking_payload
from studyspace import __version__

SEEDED_ROOM_IDS = {
    "WA-201",
    "WA-204",
    "WA-206",
    "WA-210",
    "WA-212",
    "WZ-101",
    "WZ-103",
    "WZ-105",
    "WZ-107",
    "WZ-109",
}


class HealthAndCatalogueTests(ServerTestCase):
    """FR-01 and FR-10."""

    def test_health_reports_ok_and_version(self) -> None:
        status, body = self.api.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok", "version": __version__})

    def test_room_catalogue_returns_ten_seeded_rooms(self) -> None:
        status, body = self.api.request("GET", "/api/rooms")
        self.assertEqual(status, 200)
        self.assertIsNotNone(body)
        assert body is not None  # narrow the type for static checkers
        self.assertEqual(body["count"], 10)
        rooms = body["rooms"]
        self.assertEqual({room["id"] for room in rooms}, SEEDED_ROOM_IDS)
        self.assertEqual({room["building"] for room in rooms}, {"WA", "WZ"})
        for room in rooms:
            self.assertTrue(
                {"id", "name", "building", "capacity", "features"} <= set(room)
            )
            self.assertGreaterEqual(room["capacity"], 2)
            self.assertLessEqual(room["capacity"], 10)
            self.assertTrue(room["features"])


class BuildingFilterTests(ServerTestCase):
    """Iteration 2: free-room search can be limited to one building."""

    def test_search_filters_to_one_building(self) -> None:
        status, body = self.api.request(
            "GET",
            f"/api/rooms?start={BOOKING_DAY}T10:00:00&end={BOOKING_DAY}T11:00:00"
            "&min_capacity=1&building=WA",
        )
        self.assertEqual(status, 200)
        rooms = body["rooms"]
        self.assertEqual(len(rooms), 5)
        self.assertEqual({room["building"] for room in rooms}, {"WA"})
        self.assertEqual(body["count"], 5)

    def test_unknown_building_returns_no_rooms(self) -> None:
        status, body = self.api.request(
            "GET",
            f"/api/rooms?start={BOOKING_DAY}T10:00:00&end={BOOKING_DAY}T11:00:00"
            "&min_capacity=1&building=ZZ",
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["rooms"], [])


class RoomAdminTests(ServerTestCase):
    """The staff page can add a room to the catalogue."""

    def test_create_room_returns_201_and_appears_in_catalogue(self) -> None:
        status, body = self.api.request(
            "POST",
            "/api/rooms",
            {
                "id": "WA-301",
                "name": "WA-301 Study Room",
                "building": "WA",
                "capacity": 6,
                "features": ["whiteboard", "monitor"],
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["id"], "WA-301")
        status, catalogue = self.api.request("GET", "/api/rooms")
        self.assertEqual(status, 200)
        self.assertIn("WA-301", {room["id"] for room in catalogue["rooms"]})
        self.assertEqual(catalogue["count"], 11)

    def test_duplicate_room_returns_409(self) -> None:
        payload = {
            "id": "WA-201",
            "name": "Duplicate",
            "building": "WA",
            "capacity": 4,
            "features": [],
        }
        status, body = self.api.request("POST", "/api/rooms", payload)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["code"], "room_exists")

    def test_invalid_room_returns_400(self) -> None:
        status, body = self.api.request(
            "POST",
            "/api/rooms",
            {"id": "", "name": "", "building": "", "capacity": 0, "features": []},
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "invalid_room")


class AllBookingsTests(ServerTestCase):
    """The staff view lists bookings across dates."""

    def test_all_flag_returns_bookings_from_every_date(self) -> None:
        for day in ("2026-11-05", "2026-11-06"):
            status, _ = self.api.request(
                "POST",
                "/api/bookings",
                booking_payload(start=f"{day}T10:00:00", end=f"{day}T11:00:00"),
            )
            self.assertEqual(status, 201)
        status, body = self.api.request("GET", "/api/bookings?all=1")
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 2)
        self.assertEqual(
            {booking["start"][:10] for booking in body["bookings"]},
            {"2026-11-05", "2026-11-06"},
        )


class OverlapExplanationTests(ServerTestCase):
    """A refused overlap explains itself and offers a way out."""

    def _first_booking(self):
        status, _ = self.api.request("POST", "/api/bookings", booking_payload())
        self.assertEqual(status, 201)

    def test_overlap_returns_conflict_and_alternatives(self) -> None:
        self._first_booking()
        status, body = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(
                start=f"{BOOKING_DAY}T10:30:00", end=f"{BOOKING_DAY}T11:30:00"
            ),
        )
        self.assertEqual(status, 409)
        details = body["error"]["details"]
        self.assertEqual(details["conflict"]["room_id"], "WA-201")
        self.assertEqual(details["conflict"]["start"], f"{BOOKING_DAY}T10:00:00")
        self.assertIsNotNone(details["next_free"])
        self.assertTrue(details["other_rooms"])
        self.assertNotIn(
            "WA-201", {room["room_id"] for room in details["other_rooms"]}
        )

    def test_next_free_slot_is_actually_bookable(self) -> None:
        self._first_booking()
        _, body = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(
                start=f"{BOOKING_DAY}T10:30:00", end=f"{BOOKING_DAY}T11:30:00"
            ),
        )
        next_free = body["error"]["details"]["next_free"]
        self.assertIsNotNone(next_free)
        status, _ = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(
                start=next_free["start"], end=next_free["end"]
            ),
        )
        self.assertEqual(status, 201)

    def test_suggested_other_room_is_actually_bookable(self) -> None:
        self._first_booking()
        _, body = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(
                start=f"{BOOKING_DAY}T10:30:00", end=f"{BOOKING_DAY}T11:30:00"
            ),
        )
        suggestion = body["error"]["details"]["other_rooms"][0]
        status, _ = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(
                room_id=suggestion["room_id"],
                start=suggestion["start"],
                end=suggestion["end"],
            ),
        )
        self.assertEqual(status, 201)


class WaitlistTests(ServerTestCase):
    """A refused booking can join a waitlist, and a cancellation promotes it."""

    def _book(self, room_id="WA-201", name="Alex Student", email="alex@autuni.ac.nz",
              start=f"{BOOKING_DAY}T10:00:00", end=f"{BOOKING_DAY}T11:00:00"):
        status, body = self.api.request(
            "POST",
            "/api/bookings",
            booking_payload(room_id=room_id, name=name, email=email, start=start, end=end),
        )
        self.assertEqual(status, 201)
        return body

    def test_join_waitlist_when_slot_is_taken(self) -> None:
        self._book()
        status, body = self.api.request(
            "POST",
            "/api/waitlist",
            booking_payload(
                name="Bea Wait",
                email="bea@autuni.ac.nz",
                start=f"{BOOKING_DAY}T10:30:00",
                end=f"{BOOKING_DAY}T11:30:00",
            ),
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["position"], 1)
        self.assertEqual(body["room_id"], "WA-201")

    def test_waitlist_rejects_a_free_slot(self) -> None:
        status, body = self.api.request(
            "POST",
            "/api/waitlist",
            booking_payload(start=f"{BOOKING_DAY}T14:00:00", end=f"{BOOKING_DAY}T15:00:00"),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "room_free")

    def test_waitlist_rejects_a_duplicate_entry(self) -> None:
        self._book()
        payload = booking_payload(
            name="Bea Wait",
            email="bea@autuni.ac.nz",
            start=f"{BOOKING_DAY}T10:30:00",
            end=f"{BOOKING_DAY}T11:30:00",
        )
        first, _ = self.api.request("POST", "/api/waitlist", payload)
        second, body = self.api.request("POST", "/api/waitlist", payload)
        self.assertEqual(first, 201)
        self.assertEqual(second, 409)
        self.assertEqual(body["error"]["code"], "already_waiting")

    def test_cancellation_promotes_the_first_waiting_window(self) -> None:
        booking = self._book()
        status, _ = self.api.request(
            "POST",
            "/api/waitlist",
            booking_payload(
                name="Bea Wait",
                email="bea@autuni.ac.nz",
                start=f"{BOOKING_DAY}T10:30:00",
                end=f"{BOOKING_DAY}T11:30:00",
            ),
        )
        self.assertEqual(status, 201)
        status, body = self.api.request("DELETE", f"/api/bookings/{booking['id']}")
        self.assertEqual(status, 200)
        promoted = body["promoted"]
        self.assertEqual(promoted["name"], "Bea Wait")
        self.assertEqual(promoted["start"], f"{BOOKING_DAY}T10:30:00")
        status, listing = self.api.request(
            "GET", f"/api/bookings?date={BOOKING_DAY}"
        )
        self.assertEqual([row["name"] for row in listing["bookings"]], ["Bea Wait"])
        status, entries = self.api.request("GET", "/api/waitlist")
        self.assertEqual(entries["count"], 0)


class BookingApiTests(ServerTestCase):
    """FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09."""

    def test_search_returns_free_rooms_filtered_by_capacity(self) -> None:
        status, created = self.api.request("POST", "/api/bookings", booking_payload())
        self.assertEqual(status, 201)
        self.assertIsNotNone(created)

        status, body = self.api.request(
            "GET",
            "/api/rooms?start=2026-11-05T10:00:00&end=2026-11-05T11:00:00"
            "&min_capacity=1",
        )
        self.assertEqual(status, 200)
        assert body is not None
        self.assertNotIn("WA-201", [room["id"] for room in body["rooms"]])
        self.assertEqual(body["count"], 9)

        status, body = self.api.request(
            "GET",
            "/api/rooms?start=2026-11-05T10:00:00&end=2026-11-05T11:00:00"
            "&min_capacity=9",
        )
        self.assertEqual(status, 200)
        assert body is not None
        self.assertEqual(
            {room["id"] for room in body["rooms"]}, {"WA-210", "WZ-109"}
        )

    def test_create_list_and_cancel_booking(self) -> None:
        status, created = self.api.request("POST", "/api/bookings", booking_payload())
        self.assertEqual(status, 201)
        assert created is not None
        booking_id = created["id"]
        self.assertEqual(created["room_id"], "WA-201")
        self.assertEqual(created["email"], "alex.student@autuni.ac.nz")

        status, listed = self.api.request("GET", "/api/bookings?date=2026-11-05")
        self.assertEqual(status, 200)
        assert listed is not None
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["bookings"][0]["id"], booking_id)

        status, body = self.api.request("DELETE", f"/api/bookings/{booking_id}")
        self.assertEqual(status, 204)
        self.assertIsNone(body)

        status, listed = self.api.request("GET", "/api/bookings?date=2026-11-05")
        self.assertEqual(status, 200)
        assert listed is not None
        self.assertEqual(listed["count"], 0)

        # The slot becomes bookable again after cancellation (FR-08).
        status, _ = self.api.request("POST", "/api/bookings", booking_payload())
        self.assertEqual(status, 201)

    def test_validation_errors_use_the_json_error_contract(self) -> None:
        cases = [
            (booking_payload(start="2026-11-05T10:00:00", end="2026-11-05T10:15:00"), "duration"),
            (booking_payload(start="2026-11-05T06:30:00", end="2026-11-05T07:30:00"), "opening_hours"),
            (booking_payload(start="2026-11-05T10:07:00", end="2026-11-05T11:07:00"), "slot_alignment"),
            (booking_payload(start="2026-11-03T10:00:00", end="2026-11-03T11:00:00"), "past_booking"),
            (dict(booking_payload(), room_id="ZZ-999"), "room_not_found"),
        ]
        for payload, expected_code in cases:
            with self.subTest(code=expected_code):
                status, body = self.api.request("POST", "/api/bookings", payload)
                expected_status = 404 if expected_code == "room_not_found" else 400
                self.assertEqual(status, expected_status)
                assert body is not None
                self.assertEqual(body["error"]["code"], expected_code)
                self.assertTrue(body["error"]["message"])

        # Malformed JSON is reported as 422 with the same envelope.
        status, body = self.api.request_raw("POST", "/api/bookings", b"{not json")
        self.assertEqual(status, 422)
        assert body is not None
        self.assertEqual(body["error"]["code"], "invalid_json")

    def test_daily_limit_returns_409_and_creates_no_record(self) -> None:
        first = booking_payload(
            start="2026-11-05T10:00:00", end="2026-11-05T11:00:00"
        )
        second = booking_payload(
            start="2026-11-05T11:00:00", end="2026-11-05T12:00:00"
        )
        third = booking_payload(
            start="2026-11-05T12:00:00", end="2026-11-05T13:00:00"
        )
        self.assertEqual(self.api.request("POST", "/api/bookings", first)[0], 201)
        self.assertEqual(self.api.request("POST", "/api/bookings", second)[0], 201)
        status, body = self.api.request("POST", "/api/bookings", third)
        self.assertEqual(status, 409)
        assert body is not None
        self.assertEqual(body["error"]["code"], "daily_limit")

        status, listed = self.api.request("GET", "/api/bookings?date=2026-11-05")
        assert listed is not None
        self.assertEqual(listed["count"], 2)

    def test_overlap_returns_409_and_creates_no_record(self) -> None:
        first = booking_payload(
            start="2026-11-05T10:00:00", end="2026-11-05T11:00:00"
        )
        overlapping = booking_payload(
            email="sam.student@autuni.ac.nz",
            start="2026-11-05T10:30:00",
            end="2026-11-05T11:30:00",
        )
        self.assertEqual(self.api.request("POST", "/api/bookings", first)[0], 201)

        status, body = self.api.request("POST", "/api/bookings", overlapping)
        self.assertEqual(status, 409)
        assert body is not None
        self.assertEqual(body["error"]["code"], "overlap")

        # The rejected request must not have created a record.
        status, listed = self.api.request("GET", "/api/bookings?date=2026-11-05")
        assert listed is not None
        self.assertEqual(listed["count"], 1)

        # Adjacent slots are allowed (FR-03 acceptance criterion).
        adjacent = booking_payload(
            email="sam.student@autuni.ac.nz",
            start="2026-11-05T11:00:00",
            end="2026-11-05T12:00:00",
        )
        status, _ = self.api.request("POST", "/api/bookings", adjacent)
        self.assertEqual(status, 201)


if __name__ == "__main__":
    unittest.main()
