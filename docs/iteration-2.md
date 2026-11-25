# Iteration 2 - quality, process improvement and the building filter

Iteration 1 delivered FR-03 (overlapping bookings are refused with 409). Iteration 2
uses the evidence from Iteration 1 to improve both the product and the way the team
works.

## Goal

Close the two gaps found in the Iteration 1 retrospective:

1. A review comment asked whether the interval was half-open; the issue had not said
   so explicitly. The process did not require boundary cases in the acceptance
   criteria.
2. The plan set a latency target (p95 under 300 ms) but nothing measured it, so the
   target could not be shown to hold.

## Increment

FR-11: free-room search can be limited to a building.

- `GET /api/rooms?...&building=WA` filters the result; unknown buildings return an
  empty list rather than an error.
- The search form has a building selector (All / WA / WZ).
- Two new integration tests cover the filter and the unknown-building case.

## Process improvement

**Problem (evidence from Iteration 1):** the PR review asked two questions the issue
had not answered - is the interval half-open, and does the 409 use the documented
error code. Both were fixed in review, which means the acceptance criteria were
incomplete.

**Change:** the definition of done now requires, for every rule change, at least one
boundary case and one error-contract case in the tests, written before the code.

**Measured effect:**

| Measure | Iteration 1 | Iteration 2 |
|---|---|---|
| Tests | 20 | 22 |
| Boundary tests for the changed rule | 2 | 2 (kept) |
| Review questions about boundaries | 2 | 0 |

The second iteration's two new tests were written before the filter code, and the
review raised no boundary questions.

## Quality scenario: single-user latency

Environment, inputs and procedure are recorded in `docs/evidence/latency.txt`.
Summary: 100 sequential requests per endpoint on the development machine, no
concurrency.

| Endpoint | p50 | p95 | Target |
|---|---|---|---|
| GET /api/rooms | 1.11 ms | 22.44 ms | < 300 ms |
| GET /api/rooms?start&end&min_capacity | 1.78 ms | 23.80 ms | < 300 ms |
| POST /api/bookings | 10.32 ms | 30.05 ms | < 300 ms |

Limitation: sequential requests measure single-user latency, not throughput under
concurrency.

## Outcome

- 22 tests pass.
- The building filter works through the API and the web form.
- The latency target is shown to hold for the measured scenario.
- The process change is visible in the tests written for FR-11.
