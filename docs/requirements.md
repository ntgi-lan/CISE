# Requirements — StudySpace

Last updated: 5 November 2026 (after merging PR #1 and recording the release
evidence). Status shows the current implemented state of the repository.
Traceability links each requirement to a backlog item, an implementation file and
a named test.

## Functional requirements

| ID | Requirement | Priority | Acceptance criteria | Status |
|---|---|---|---|---|
| FR-01 | Show the room catalogue (id, building, capacity, features) | Must | `GET /api/rooms` returns the 10 seeded rooms with all fields; each room has a stable id | Implemented |
| FR-02 | Search rooms free for a date and time window, filtered by minimum capacity | Must | Given a valid window and capacity, only rooms with no overlapping booking and sufficient capacity are returned; invalid input returns 400 | Implemented |
| FR-03 | Reject overlapping bookings for the same room | Must | Given an existing booking 10:00–11:00, `POST` 10:30–11:30 for the same room returns 409 and creates no record; adjacent 11:00–12:00 returns 201 | Implemented (Issue #4, PR #1) |
| FR-04 | Enforce opening hours and 15-minute slot boundaries | Must | A booking outside opening hours or with a non-15-minute boundary returns 400 with an error code | Implemented |
| FR-05 | Enforce 30–120 minute duration | Must | 15-minute and 150-minute requests return 400; 30 and 120 minute requests succeed | Implemented |
| FR-06 | Reject bookings in the past | Must | A start time earlier than the current local time returns 400 | Implemented |
| FR-07 | Limit a user (email) to two future bookings per day | Should | A third future booking for the same email and date returns 409 | Implemented |
| FR-08 | Cancel a booking | Should | `DELETE /api/bookings/{id}` returns 204, removes the record, and the slot becomes bookable again | Implemented |
| FR-09 | List bookings for a date | Could | `GET /api/bookings?date=YYYY-MM-DD` returns that date's bookings ordered by start time | Implemented |
| FR-10 | Health endpoint for automated checks | Must | `GET /api/health` returns 200 with `{"status": "ok", "version": "0.1.0"}` | Implemented |

### Runtime rules (SPEC section 3)

- Mon–Fri 07:00–22:00; Sat–Sun 09:00–18:00.
- 15-minute boundaries for start and end.
- Duration between 30 and 120 minutes inclusive.
- Overlapping bookings for the same room rejected with 409.
- No booking may start in the past.
- At most two future bookings per email per date.

## Non-functional requirements

| ID | Requirement | Measure | Status |
|---|---|---|---|
| NFR-01 | Portability / reproducibility | A fresh checkout runs on Python 3.12 with the standard library only; `python -m unittest discover -s tests` passes | Implemented |
| NFR-02 | Performance | p95 API latency under 300 ms on the reference laptop for a warm local server (manual measurement, recorded) | To measure in Iteration 1 |
| NFR-03 | Usability | 4 of 5 first-time testers complete one booking without help (manual check) | Planned for Iteration 2 |
| NFR-04 | Maintainability | Booking rules isolated in `studyspace/rules.py`; each rule covered by at least one named test | Implemented |

## Traceability matrix

| Requirement | Backlog | Implementation | Test |
|---|---|---|---|
| FR-01 | US-01, US-10 | `studyspace/storage.py::load_rooms`, `studyspace/server.py::_rooms_payload` | `test_api.HealthAndCatalogueTests.test_room_catalogue_returns_ten_seeded_rooms` |
| FR-02 | US-02 | `studyspace/rules.py::rooms_free_for_window`, `studyspace/server.py::_rooms_payload` | `test_api.BookingApiTests.test_search_returns_free_rooms_filtered_by_capacity` |
| FR-03 | US-04b | `studyspace/rules.py::check_overlap`, called by `studyspace/server.py::_create_booking` | `test_rules.OverlapTests.test_overlapping_booking_for_the_same_room_is_rejected`, `test_adjacent_slots_and_other_rooms_do_not_overlap`, `test_overlap_check_has_no_side_effect`; `test_api.BookingApiTests.test_overlap_returns_409_and_creates_no_record` |
| FR-04 | US-03 | `studyspace/rules.py::validate_opening_hours`, `validate_slot_alignment` | `test_rules.test_weekday_booking_before_opening_is_rejected`, `test_weekday_booking_after_closing_is_rejected`, `test_weekend_opening_hours_are_enforced`, `test_unaligned_slot_boundary_is_rejected` |
| FR-05 | US-04a | `studyspace/rules.py::validate_duration` | `test_rules.test_duration_shorter_than_thirty_minutes_is_rejected`, `test_duration_longer_than_two_hours_is_rejected`, `test_duration_boundaries_of_thirty_and_one_hundred_and_twenty_are_allowed` |
| FR-06 | US-04a | `studyspace/rules.py::validate_not_in_past` | `test_rules.PastBookingTests.test_booking_in_the_past_is_rejected` |
| FR-07 | US-07 | `studyspace/rules.py::check_daily_limit` | `test_rules.DailyLimitTests.test_third_future_booking_for_the_same_email_is_rejected` |
| FR-08 | US-05 | `studyspace/storage.py::BookingStorage.delete`, `studyspace/server.py::_delete_booking` | `test_api.BookingApiTests.test_create_list_and_cancel_booking` |
| FR-09 | US-06 | `studyspace/storage.py::BookingStorage.list_for_date`, `studyspace/server.py::_bookings_payload` | `test_api.BookingApiTests.test_create_list_and_cancel_booking` |
| FR-10 | US-08 | `studyspace/server.py::_handle_api` | `test_api.HealthAndCatalogueTests.test_health_reports_ok_and_version` |
| NFR-01 | US-11 | repository-wide | full suite via `python -m unittest discover -s tests -v` (20 tests, all passing) |
| NFR-04 | US-11 | `studyspace/rules.py` | all `test_rules` cases |

## Out of scope

AUT single sign-on, payments, room hardware, notifications, native apps,
multi-campus support, analytics dashboards, and a rules administration UI. See
the scope section of the project definition in the assignment report.
