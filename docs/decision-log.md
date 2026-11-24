# Decision log — StudySpace

Short architecture-decision records (ADR style). Each decision lists the context,
the decision, the consequences, the alternatives that were rejected and the member
who owns it (Group Passion, four-person team).

## DL-001 — Python 3.12 standard library only

**Owner.** Haoguang Wang

**Context.** The assessment environment may be offline and the submission must be
reproducible by an assessor on a fresh machine. A four-person student team with a
limited weekly budget cannot maintain an extra toolchain.

**Decision.** The application and its tests use only the Python 3.12 standard
library (`http.server`, `sqlite3`, `json`, `unittest`, `urllib`). No third-party
packages, no build step, no virtualenv.

**Consequences.** A fresh checkout runs with one command. The HTTP layer is
minimal, so request parsing and routing are written by hand and must stay small.
No dependency vulnerabilities or version drift to manage.

**Alternatives rejected.** Flask/Django (dependency install and offline risk);
Node/React (build step and a second runtime); a static mock (not a working
system).

## DL-002 — `ThreadingHTTPServer` with a small hand-written router

**Owner.** Jiawei Zhang

**Context.** The API has six endpoints. Requests must not block each other during
a demo, and the integration tests need a real socket.

**Decision.** Subclass `ThreadingHTTPServer` and dispatch on method and path in a
single handler, mapping `RuleViolation` to the JSON error envelope in one place.

**Consequences.** About 350 lines of transport code, fully understood and
testable with `urllib` against an ephemeral port. The same code path runs in
tests and in the demo.

**Alternatives rejected.** `wsgiref` (another abstraction without a benefit at
this size); a third-party framework (breaks DL-001).

## DL-003 — SQLite via `sqlite3`, one connection per operation

**Owner.** Jiawei Zhang

**Context.** Bookings must persist across restarts, and the environment cannot run
a database server.

**Decision.** Store bookings in a SQLite file using short-lived connections per
operation. The schema is created on start-up; four operations are needed (create,
get, list-for-date, delete).

**Consequences.** Thread-safe around the threaded server without a pool. Queries
are simple and the database file can be inspected with any SQLite tool. Timestamps
are stored as ISO-8601 text so they sort lexicographically.

**Alternatives rejected.** In-memory dictionaries (lost on restart, weak evidence
of persistence); JSON files (no concurrent-write safety); an external database
server (out of scope, no budget).

## DL-004 — Booking rules isolated as pure functions

**Owner.** Jiawei Zhang

**Context.** Requirements are expected to change after lecturer feedback (the
rule set is the most volatile part of the system), and the team cannot afford
broad rework in the week before the deadline.

**Decision.** Put every rule in `studyspace/rules.py` as a pure function that
takes values and a "now" and raises `RuleViolation(code, message, status)`. The
server composes the rules; storage and HTTP know nothing about them.

**Consequences.** Rules are unit-tested without a server or database; each error
code is defined once; a rule change is a small, reviewable diff plus one test.
NFR-04 is directly verifiable by the module's existence and its test file.

**Alternatives rejected.** Rule checks inline in request handlers (untestable
without HTTP); a rules engine/DSL (over-engineering for about eight rules).

## DL-005 — Stable JSON error contract with machine-readable codes

**Owner.** Lei Wen

**Context.** The browser must show a useful message for any rejected booking, and
the tests must assert the reason, not just the status. The report also needs a
clear integration story for the "shown free but rejected" race.

**Decision.** Every error is
`{"error": {"code": "...", "message": "..."}}` with one stable code per failure
(`duration`, `slot_alignment`, `opening_hours`, `past_booking`, `daily_limit`,
`overlap`, `invalid_json`, ...) and the HTTP status stated in the SPEC.
`RuleViolation` carries both.

**Consequences.** The browser can map codes to messages later; tests assert the
exact code; the error contract is a review checklist item for every PR.

**Alternatives rejected.** Bare HTTP status with an HTML error page (unusable for
fetch); free-text messages only (not assertable, drifts between endpoints).

## DL-006 — Git bundle delivery, GitHub Flow for the trial change

**Owner.** Haoguang Wang

**Context.** The team has no GitHub account and the assignment requires evidence
of a collaborative workflow. There is no remote to host pull requests.

**Decision.** Version the work with Git locally on `main`. Record the trial change
with a short-lived feature branch, two focused commits, a written PR record with a
review checklist and a recorded review conversation, a `--no-ff` merge and a
release tag (`v0.1.0`). Deliver the repository as `studyspace.bundle` (plus a zip
of the working tree) so an assessor can clone the full history offline. The PR
record and review checklist stand in for a hosted pull request: the review was
performed by Boyi Jiang, a member other than the author, and the merge was
approved by Haoguang Wang.

**Consequences.** The full history is verifiable offline. The workflow discipline
(issue, branch, small commits, independent review, merge commit, tag) is
exercised and evidenced without fabricating a hosted URL or an account.

**Alternatives rejected.** A fake GitHub URL (academic-integrity issue); merging
directly to `main` without a record (no workflow evidence); `git push` to an
unknown remote (no network and no account).
