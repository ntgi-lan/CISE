# StudySpace

StudySpace is a small web application that lets AUT students find a free study
room on the city campus and claim it for a time slot. It replaces the informal
whiteboard and group-chat bookings that cause double bookings and wasted trips
between classes.

This repository is the assessed artefact for Software Engineering Assignment 1
(AUT), delivered by **Group Passion**, a four-person student team. The repository was
assembled and submitted by **Lei Wen (25307866)** on the group's behalf; the contribution
log records the group's roles and hours. It is a working
application, not a mock-up: the HTTP API, the rule engine and the SQLite database
are real, and the test suite drives them over HTTP.

## Team

| Member | Student ID | Email | Role |
|---|---|---|---|
| Haoguang Wang | 25305403 | zcz6356@autuni.ac.nz | Group leader / product owner: scope, backlog, priorities, acceptance criteria, risk register, chairs the iteration reviews, approves merges |
| Jiawei Zhang | 25305405 | dqx2069@autuni.ac.nz | Back-end engineer: `server.py`, `storage.py`, `models.py`, `data/rooms.json`; author of the FR-03 overlap rule |
| Lei Wen | 25307866 | wbp5373@autuni.ac.nz | Front-end and documentation lead: `studyspace/web/`, README and evidence documents, report integration, bundle verification |
| Boyi Jiang | 25307501 | myd2262@autuni.ac.nz | Tester and reviewer: unittest suite, CI configuration, reviewer of PR #2, usability and latency checks |

Work is split by component and every change is reviewed by a member other than
its author. The weekly iteration review is chaired by the product owner. Recorded
effort for the build and the workflow trial is in
[docs/contribution-log.md](docs/contribution-log.md).

## Status

All must-have requirements are implemented and covered by automated tests.

| Requirement | Summary | Status |
|---|---|---|
| FR-01 | Room catalogue (`GET /api/rooms`) | Implemented |
| FR-02 | Search rooms free for a window and capacity | Implemented |
| FR-03 | Reject overlapping bookings for the same room | Implemented (Issue #1, PR #2) |
| FR-04 | Opening hours and 15-minute slot boundaries | Implemented |
| FR-05 | 30–120 minute duration | Implemented |
| FR-06 | No bookings in the past | Implemented |
| FR-07 | Two future bookings per email per day | Implemented |
| FR-08 | Cancel a booking | Implemented |
| FR-09 | List bookings for a date | Implemented |
| FR-10 | Health endpoint | Implemented |

The overlap rule (FR-03) was the tracked requirement used for the workflow trial.
Jiawei Zhang implemented it on the short-lived branch `feature/fr03-double-booking`,
Boyi Jiang wrote the overlap tests and reviewed PR #2 against the checklist,
Haoguang Wang approved the `--no-ff` merge, and Lei Wen recorded the evidence and
verified the bundle. It was released as tag `v0.1.0`; the trail is described in
[docs/workflow-trial.md](docs/workflow-trial.md) and
[docs/pull-requests/PR-002.md](docs/pull-requests/PR-002.md).

## Quick start

Requires Python 3.12 and nothing else — the application uses the standard library
only. From the repository root:

```bash
python -m studyspace --port 8000
```

Then open <http://127.0.0.1:8000/> in a browser. The SQLite database is created at
`data/studyspace.db` on first run. Stop the server with Ctrl+C.

To use a different port or database file:

```bash
python -m studyspace --port 8080 --db data/demo.db
```

`make run` does the same thing if `make` is available.

## Tests

From the repository root:

```bash
python -m unittest discover -s tests -v
```

The suite uses the standard library only. It starts the real `ThreadingHTTPServer`
on an ephemeral port against a temporary SQLite database, so the integration tests
exercise the same code path as the running application.

The suite currently reports **20 tests, all passing**. The real output is stored
verbatim in [docs/evidence/test-results.txt](docs/evidence/test-results.txt). See
[docs/test-plan.md](docs/test-plan.md) for the test strategy and traceability.

## API

Base URL: `http://127.0.0.1:8000`

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | health probe; returns `{"status": "ok", "version": "0.1.0"}` |
| GET | `/api/rooms` | room catalogue (10 seeded rooms) |
| GET | `/api/rooms?start=<iso>&end=<iso>&min_capacity=<n>` | rooms free for a window and capacity |
| GET | `/api/bookings?date=YYYY-MM-DD` | bookings for a date, ordered by start |
| POST | `/api/bookings` | create a booking |
| DELETE | `/api/bookings/{id}` | cancel a booking |

Datetimes are local (naive) ISO-8601 values such as `2026-11-05T10:00:00`. A
booking request body looks like this:

```json
{
  "room_id": "WA-201",
  "name": "Alex Student",
  "email": "alex.student@autuni.ac.nz",
  "start": "2026-11-05T10:00:00",
  "end": "2026-11-05T11:00:00"
}
```

Errors use a stable envelope and code, for example:

```json
{"error": {"code": "duration", "message": "Bookings must last between 30 and 120 minutes."}}
```

| Status | Codes |
|---|---|
| 400 | `opening_hours`, `slot_alignment`, `duration`, `past_booking`, `invalid_attendee`, `invalid_search`, `invalid_query`, `invalid_datetime`, `invalid_request` |
| 404 | `room_not_found`, `booking_not_found`, `not_found` |
| 409 | `overlap`, `daily_limit` |
| 422 | `invalid_json`, `invalid_request`, `payload_too_large` |

## How the repository is organised

```
studyspace/
├── README.md
├── Makefile
├── .gitignore
├── .github/workflows/ci.yml
├── data/rooms.json
├── studyspace/
│   ├── __init__.py  __main__.py  server.py  rules.py  models.py  storage.py
│   └── web/index.html  app.js  styles.css
├── tests/
│   ├── __init__.py  helpers.py  test_rules.py  test_api.py
└── docs/
    ├── backlog.md  requirements.md  architecture.md  decision-log.md
    ├── risk-register.md  test-plan.md  workflow-trial.md  evidence-index.md
    ├── contribution-log.md
    ├── issues/ISSUE-001-fr03-double-booking.md
    ├── pull-requests/PR-002.md
    └── evidence/test-results.txt  manual-smoke-test.txt  repo-state.txt
```

The package layout separates the rule engine (`rules.py`, pure functions) from
persistence (`storage.py`), transport (`server.py`) and the browser client
(`studyspace/web/`). `docs/architecture.md` explains the layering and the API
contract.

## Assessor access

There is no hosted repository URL for this project: the team does not have a
GitHub account and worked in a local Git repository with no remote, so the
repository is delivered as a Git bundle (`studyspace.bundle`) inside the
submission package, together with a zip of the working tree. The bundle contains
the same history as this working tree. Clone it with:

```bash
git clone studyspace.bundle studyspace
cd studyspace
git tag
git log --oneline --graph --decorate
python -m unittest discover -s tests -v
```

The release tag `v0.1.0` marks the released evidence commit (test output, smoke
test, workflow record and the updated status/traceability documents). The
submission commit is the tip of `main` (it adds the recorded repository state);
run `git log -1 --format="%H %s"` in the clone to print it. `git status` is clean
after cloning.

## Evidence and planning documents

- [docs/backlog.md](docs/backlog.md) — product backlog with MoSCoW priorities and the split of US-04.
- [docs/requirements.md](docs/requirements.md) — functional/non-functional requirements and traceability.
- [docs/architecture.md](docs/architecture.md) — component overview, data model and API contract.
- [docs/decision-log.md](docs/decision-log.md) — design decisions (DL-001–DL-006) with owners.
- [docs/risk-register.md](docs/risk-register.md) — six risks with likelihood/impact, owners and responses.
- [docs/test-plan.md](docs/test-plan.md) — test levels, fixtures and acceptance mapping.
- [docs/workflow-trial.md](docs/workflow-trial.md) — FR-03 from tracked requirement through review, merge and tag.
- [docs/pull-requests/PR-002.md](docs/pull-requests/PR-002.md) — review checklist, review conversation and merge decision.
- [docs/evidence-index.md](docs/evidence-index.md) — assessment criterion → artefact → commit.
- [docs/evidence/test-results.txt](docs/evidence/test-results.txt) — verbatim `unittest` output (20 tests, OK).
- [docs/evidence/manual-smoke-test.txt](docs/evidence/manual-smoke-test.txt) — live HTTP smoke test of the running app.
- [docs/evidence/repo-state.txt](docs/evidence/repo-state.txt) — git log, status, tags and HEAD hash.
- [docs/contribution-log.md](docs/contribution-log.md) — effort log for the four-person team.

## Verification recorded for this release

```text
$ python -m unittest discover -s tests -v
Ran 20 tests ... OK

$ git status --short
(no output — clean working tree)

$ git tag --list
v0.1.0
```

The Git bundle was verified by cloning it into a temporary directory and running
the full suite there; the bundle header lists all branches and the tag, and the
clone contains the complete history.

## Known gaps and next steps

- No authentication: the application records a name and email only, matching the
  explicit scope exclusion for AUT single sign-on.
- Notifications, calendar sync, admin reporting and a rules administration UI are
  out of scope for this release (see `docs/decision-log.md` and the report).
- Manual checks planned for the iterations: NFR-02 latency measurement and NFR-03
  usability check, owned by Boyi Jiang (`docs/test-plan.md`).

## Constraints

- Python 3.12 standard library only; no third-party packages, no build step, no
  network access at runtime.
- Local SQLite database file, created on first run and ignored by Git.
- The demo runs locally; there is no cloud deployment.
