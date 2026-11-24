# ISSUE-001 — FR-03: reject overlapping bookings for the same room

- **Type:** tracked requirement (clear gap in the walking skeleton)
- **Status:** Closed (merged via PR #2, committed to `main`, released in `v0.1.0`)
- **Priority:** Must (MoSCoW)
- **Requirement:** FR-03
- **Backlog item:** US-04b (split from US-04 on 3 November 2026)
- **Recorded by:** Haoguang Wang (product owner), 3 November 2026
- **Assigned to:** Jiawei Zhang (back-end engineer)
- **Reviewed by:** Boyi Jiang (tester and reviewer)

## Context

The walking skeleton lets a student create a booking and rejects invalid values
(opening hours, 15-minute boundaries, duration, past start, attendee details), and
it limits one email to two future bookings per day. Search (`GET /api/rooms`) also
excludes rooms that are already busy in the requested window.

However, the **create path does not reject a booking that overlaps an existing
booking for the same room**. Two students can therefore create overlapping claims
for the same room through the API. This is exactly the double-booking problem the
project exists to solve, so FR-03 is a Must-have for the release.

The gap was found during planning when the product owner split US-04 into US-04a
(create and validate, delivered in the skeleton) and US-04b (overlap rejection,
this issue). It is deliberate: the missing rule is the small, tracked change used
to evidence the workflow trial through implementation, review, test and merge.
The acceptance criteria were reviewed by the tester before implementation so that
the author and the reviewer agreed on the expected behaviour.

## Acceptance criteria

1. **Given** an existing booking for room `WA-201` from 10:00 to 11:00,
   **when** a client posts a booking for `WA-201` from 10:30 to 11:30,
   **then** the API responds `409` with error code `overlap` and no booking is
   created.
2. **Given** the same existing booking,
   **when** a client posts a booking for `WA-201` from 11:00 to 12:00,
   **then** the API responds `201` (adjacent slots do not overlap).
3. **Given** two bookings for different rooms at the same time,
   **when** both are created,
   **then** both succeed (the rule is per room).
4. The overlap check is implemented in the pure rule module and covered by
   named unit tests, including a no-side-effect check.
5. All previous behaviour remains green: the full suite passes.
6. README, requirements and the evidence index are updated.

## Definition of done

- [x] `studyspace/rules.py` exposes an overlap rule with a docstring naming FR-03.
- [x] The create-booking path calls the rule after the daily-limit check and
      before persistence.
- [x] New tests: overlap rejected, adjacent slots allowed, no side effect; plus an
      API test for 409 and no record created.
- [x] Full suite green: `python -m unittest discover -s tests -v` (20 tests, OK).
- [x] Reviewed by Boyi Jiang against the PR checklist with the error contract
      verified (409 + `code: "overlap"`).
- [x] Merged with `--no-ff` by Haoguang Wang; merge message per SPEC; release tag
      recorded.

## Resolution

Closed 4 November 2026. The change was implemented by Jiawei Zhang on
`feature/fr03-double-booking`, with tests added by Boyi Jiang:

- `the recorded commit` — `feat(booking): reject overlapping bookings for the same room (FR-03)` (Jiawei Zhang)
- `the recorded commit` — `test(booking): cover overlap, adjacent-slot and no-side-effect cases` (Boyi Jiang)

Reviewed in [PR-002](../pull-requests/PR-002.md) by Boyi Jiang, with the merge
approved by Haoguang Wang and completed with `--no-ff` at `the recorded commit`. The full
suite was run on `main` after the merge: 20 tests, all passing
([test results](../evidence/test-results.txt)). Released as tag `v0.1.0`; see
[workflow-trial.md](../workflow-trial.md) for the complete evidence trail.
