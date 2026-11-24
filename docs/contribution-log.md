# Contribution log — StudySpace (Group Passion)

Team: **Group Passion**, four members. Recorded effort covers the repository
build and the FR-03 workflow trial (2–4 November 2026) and is used for the
contribution statements in the assignment report.

| Member | Student ID | Role | Recorded hours (2–4 Nov 2026) |
|---|---|---|---|
| Haoguang Wang | 25305403 | Group leader / product owner | 13.0 |
| Jiawei Zhang | 25305405 | Back-end engineer | 12.5 |
| Lei Wen | 25307866 | Front-end and documentation lead | 12.5 |
| Boyi Jiang | 25307501 | Tester and reviewer | 12.0 |
| | | **Total** | **50.0** |

Every change was reviewed by a member other than its author; the iteration
review was chaired by Haoguang Wang.

## Haoguang Wang — product owner

| Date | Activity | Hours |
|---|---|---|
| 2 Nov 2026 | Read the Canvas brief; define the problem, value, stakeholders, scope/exclusions and constraints | 2.0 |
| 2 Nov 2026 | Release plan: two iterations, acceptance criteria AC1–AC6, evaluation measures | 2.5 |
| 3 Nov 2026 | Product backlog with MoSCoW priorities; split US-04; record the FR-03 gap as Issue #1 and assign it to Jiawei Zhang | 2.5 |
| 3 Nov 2026 | Risk register, mitigation plan and chair of the planning review | 2.0 |
| 4 Nov 2026 | Iteration review; review of the PR #2 merge decision and approval; `--no-ff` merge | 1.5 |
| 4 Nov 2026 | Contribution log, checkpoint and sign-off of the release bundle | 2.5 |
| | **Total** | **13.0** |

## Jiawei Zhang — back-end engineer

| Date | Activity | Hours |
|---|---|---|
| 2 Nov 2026 | Architecture review; data model and JSON API contract | 2.0 |
| 3 Nov 2026 | SQLite `BookingStorage` and the seeded room loader | 2.0 |
| 3 Nov 2026 | Rule module: opening hours, slot alignment, duration, past bookings, daily limit | 3.0 |
| 4 Nov 2026 | JSON API routing, request validation and the error envelope | 3.0 |
| 4 Nov 2026 | FR-03 overlap rule (`rules.check_overlap` plus the create-path call) and PR #2 author work | 1.5 |
| 4 Nov 2026 | Defect fixes from review; requirements traceability update | 1.0 |
| | **Total** | **12.5** |

## Lei Wen — front-end and documentation lead

| Date | Activity | Hours |
|---|---|---|
| 2 Nov 2026 | Repository scaffold, README, CI workflow and Makefile | 2.0 |
| 3 Nov 2026 | Single-page front-end: search form, result cards, booking dialog, cancel button | 3.0 |
| 3 Nov 2026 | Requirements and test-plan documents | 1.5 |
| 4 Nov 2026 | Workflow-trial record, evidence index and PR overview maintenance | 2.0 |
| 4 Nov 2026 | Evidence regeneration: test output, live smoke-test transcript, repository-state record | 2.0 |
| 4 Nov 2026 | Git bundle build and clone verification; absolute-path and secret check | 2.0 |
| | **Total** | **12.5** |

## Boyi Jiang — tester and reviewer

| Date | Activity | Hours |
|---|---|---|
| 2 Nov 2026 | Test strategy and CI configuration review | 1.5 |
| 3 Nov 2026 | Unit tests for the booking rules (10 baseline tests) | 2.5 |
| 3 Nov 2026 | Integration tests for the HTTP API (6 baseline tests) | 2.5 |
| 4 Nov 2026 | FR-03 overlap tests: three rule tests and one API test | 2.0 |
| 4 Nov 2026 | PR #2 review against the checklist, including the recorded review conversation | 1.5 |
| 4 Nov 2026 | Full-suite runs, defect report, latency and usability check plan | 2.0 |
| | **Total** | **12.0** |

## Planned effort for the two iterations

Each member plans 12 hours for the two iterations (Iteration 1: 5–8 November
2026; Iteration 2: 9–12 November 2026), 48 hours in total, within the 12–15 hour
per-week budget stated in the project definition.

## AI-use disclosure

Generative AI assistance was used by the team to help draft code and
documentation in this repository. The output was executed and tested, and the
recorded test results and command outputs are real runs, not generated text. This
disclosure is repeated in the README and in the assignment report.
