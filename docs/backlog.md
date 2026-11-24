# StudySpace product backlog

Owner: Lei Wen (individual submission). Last updated: 5 November
2026 (after the FR-03 workflow trial merge and release tag).

Priorities use MoSCoW. Estimates are ideal engineering hours for the member who
owns the item. The "Iteration" column records where the item is planned and
verified; the walking skeleton built during the 3–4 November workflow trial
already contains most of the code, and the iterations re-verify and extend it.
Owners: HW = Lei Wen, JZ = Lei Wen, LW = Lei Wen, BJ = Lei Wen.

| ID | User story | Priority | Estimate (h) | Iteration | Status | Owner | Requirements |
|---|---|---|---|---|---|---|---|
| US-01 | As a student, I can view the room catalogue so that I know which rooms exist. | Must | 3 | 1 | Done | JZ | FR-01 |
| US-02 | As a student, I can search for rooms free in a time window with a minimum capacity, so that I only travel to a room I can use. | Must | 4 | 1 | Done | JZ | FR-02 |
| US-03 | As the room owner, the system rejects bookings outside opening hours or off the 15-minute grid, so that rooms are used only in bookable slots. | Must | 3 | 1 | Done | JZ | FR-04 |
| US-04a | As a student, I can create a booking for a room and time slot, with duration, past-time and attendee validation, so that my claim is recorded. | Must | 4 | 1 | Done | JZ | FR-05, FR-06 |
| US-04b | As a student, the system rejects a booking that overlaps an existing booking for the same room, so that double bookings cannot happen. | Must | 2 | 1 | Done — PR #1 (author JZ, reviewer BJ, merge approved by HW), merge `9dda54a`, tag `v0.1.0` | JZ (tests BJ) | FR-03 |
| US-05 | As a student, I can cancel a booking so that the room becomes available again. | Should | 2 | 2 | Done | JZ | FR-08 |
| US-06 | As a student, I can list the bookings for a date so that I can see what is taken. | Could | 2 | 2 | Done | JZ | FR-09 |
| US-07 | As the room owner, one email can hold at most two future bookings per day, so that a single user cannot hoard rooms. | Should | 2 | 2 | Done | JZ | FR-07 |
| US-08 | As an assessor or operator, I can call a health endpoint so that automated checks can confirm the service is up. | Must | 1 | 1 | Done | JZ | FR-10 |
| US-09 | As a student, I can search, book and cancel from a web page so that I do not need to use curl. | Must | 6 | 2 | Done (basic single page) | LW | FR-01, FR-02, FR-08 |
| US-10 | As a developer, I can seed 10 rooms in 2 buildings from JSON so that the demo needs no manual data entry. | Must | 1 | 1 | Done | JZ | FR-01 |
| US-11 | As a developer, I have an automated unit and integration test suite so that rule changes are safe under time pressure. | Must | 5 | 1–2 | Done (20 tests, all passing) | BJ | NFR-01, NFR-04 |
| US-12 | As the team, I have planning and workflow documentation so that the assessment can trace decisions and evidence. | Must | 5 | 1–2 | Done (trial evidence recorded) | LW | Process |

## Split of US-04 (recorded 3 November 2026)

US-04 ("Create a booking for a room and time slot") is too large to review as one
change, so planning (Lei Wen) split it into two slices:

- **US-04a** — parse and validate the request (attendee, duration, slot boundary,
  opening hours, past start), enforce the per-email daily limit, persist the
  booking. Delivered in the walking skeleton by Lei Wen.
- **US-04b** — reject a booking that overlaps an existing booking for the same
  room (FR-03). The acceptance criteria are written in
  [Issue #4](issues/ISSUE-004-fr03-double-booking.md). The gap is deliberate: it
  is the tracked requirement used for the workflow trial, so it is implemented on a
  short-lived branch, reviewed against the checklist and merged rather than being
  part of the skeleton.

## Outcome of the split (4 November 2026)

US-04b was completed on branch `feature/fr03-double-booking` in two commits:
`e7f073e` (production change) and `481cb06` (tests). It was reviewed against the
checklist in [PR-001](pull-requests/PR-001.md), merged with `--no-ff` at
`9dda54a`, and the evidence commit was tagged `v0.1.0`. The gap is now closed and
FR-03 is covered by three rule tests and one integration test.

## Definition of ready (used when pulling an item into an iteration)

- Written as a user story with a MoSCoW priority and a named owner.
- Acceptance criteria expressed as Given/When/Then and mapped to a requirement ID.
- No unresolved dependency on an open issue.
- Small enough for one short-lived branch and one review by another member.

## Definition of done (applies to every item)

- Implementation follows the rules in `studyspace/rules.py` or the storage/HTTP
  layer as appropriate.
- At least one named automated test covers the acceptance criteria.
- `python -m unittest discover -s tests -v` passes with no failures.
- README, requirements and architecture documents updated where behaviour
  changed.
- Reviewed by a member other than the author against the checklist in
  `docs/pull-requests/PR-001.md` and merged with `--no-ff`.
