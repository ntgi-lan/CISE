# Test plan — StudySpace

Last updated: 5 November 2026 (FR-03 tests merged; 20 tests total). Test suite
owned by Lei Wen (tester and reviewer); evidence recorded by Lei Wen.

## Objective

Provide repeatable evidence that the booking rules and the HTTP API behave as
specified, so that rule changes under time pressure cannot silently regress.
This directly addresses engineering issue 3 (software quality under time
pressure) and NFR-01/NFR-04.

## Environment

- Python 3.12, standard library only (`unittest`, `urllib`, `sqlite3`,
  `tempfile`, `threading`).
- No network access required; no packages to install.
- Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Test levels

| Level | File | Scope | Fixture | Owner |
|---|---|---|---|---|
| Unit | `tests/test_rules.py` | Pure booking rules: opening hours, slot boundaries, duration, past bookings, daily limit, overlap | None; fixed datetimes and an injected `now` | Lei Wen |
| Integration | `tests/test_api.py` | Real HTTP server on an ephemeral port, real SQLite temporary database, JSON contract, status codes | `tests/helpers.py` starts a `ThreadingHTTPServer` per test with a temporary database and a pinned clock | Lei Wen |
| Manual smoke | see below | Start the app and exercise health, create, overlap rejection and cancel through the API | Local server on a chosen port | Lei Wen |

The integration fixture injects a fixed clock (Wednesday 4 November 2026, 08:00)
so that "future" and "past" dates are deterministic whenever the suite runs. The
server itself uses `datetime.now()` in normal operation.

## Test data

- The 10-room catalogue is the real seed file (`data/rooms.json`), loaded through
  the production loader.
- Each integration test gets a brand-new temporary SQLite database. Tests never
  touch `data/studyspace.db`.
- Booking windows always use the fixed test day (Thursday 5 November 2026) and
  15-minute-aligned times.

## Coverage by acceptance criterion

| Requirement | Test(s) |
|---|---|
| FR-01 catalogue | `test_api.HealthAndCatalogueTests.test_room_catalogue_returns_ten_seeded_rooms` |
| FR-02 search | `test_api.BookingApiTests.test_search_returns_free_rooms_filtered_by_capacity` |
| FR-03 overlap | `test_rules.OverlapTests.test_overlapping_booking_for_the_same_room_is_rejected`, `test_adjacent_slots_and_other_rooms_do_not_overlap`, `test_overlap_check_has_no_side_effect`; `test_api.BookingApiTests.test_overlap_returns_409_and_creates_no_record` |
| FR-04 hours/slots | `test_rules.OpeningHoursTests.*`, `test_rules.SlotAndDurationTests.test_unaligned_slot_boundary_is_rejected` |
| FR-05 duration | `test_rules.SlotAndDurationTests.test_duration_*` |
| FR-06 past | `test_rules.PastBookingTests.test_booking_in_the_past_is_rejected`, validation integration case |
| FR-07 daily limit | `test_rules.DailyLimitTests.test_third_future_booking_for_the_same_email_is_rejected`, integration case |
| FR-08 cancel | `test_api.BookingApiTests.test_create_list_and_cancel_booking` |
| FR-09 list | `test_api.BookingApiTests.test_create_list_and_cancel_booking`, daily-limit integration case |
| FR-10 health | `test_api.HealthAndCatalogueTests.test_health_reports_ok_and_version` |
| Error contract | `test_api.BookingApiTests.test_validation_errors_use_the_json_error_contract` (400/404/409/422 and codes) |

## Pass criteria

- 100% of tests pass; zero errors and zero failures. The released suite has
  20 tests and reports `OK`.
- Every FR has at least one named test.
- The full suite runs in under 10 seconds on the reference laptop.
- Real output is saved verbatim to `docs/evidence/test-results.txt`; it is never
  edited by hand.

## Manual smoke test (demo)

From the repository root, with the server running on port 8000:

```bash
python -m studyspace --port 8000
```

In a second terminal:

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"room_id":"WA-201","name":"Alex Student","email":"alex.student@autuni.ac.nz","start":"2026-11-05T10:00:00","end":"2026-11-05T11:00:00"}'
curl -X DELETE http://127.0.0.1:8000/api/bookings/1
```

Expected: the health probe returns `{"status": "ok", "version": "0.1.0"}`; the
create returns 201 with the booking JSON; a second overlapping create returns 409
with code `overlap`; the delete returns 204 and the booking list for the date is
empty. On Windows PowerShell use `Invoke-RestMethod` with the same URLs and JSON
body.

Real smoke-test output is stored in `docs/evidence/manual-smoke-test.txt`.

## NFR-02 performance check (manual)

With a warm local server, time a small loop of health, room-search and booking
requests (owner: Lei Wen). Record the p95 in the report's evaluation section.
This is a manual check, not part of the automated suite.

## What is not tested automatically

- Browser rendering and usability (NFR-03) — manual usability check in
  Iteration 2, owned by Lei Wen with Lei Wen observing.
- Cross-browser behaviour; the front-end is vanilla JavaScript and the API is
  covered independently.
- Performance under load — out of scope for a single-campus demo.
