# StudySpace — room booking for AUT students

StudySpace lets AUT students find a free study room and claim it for a time slot. It replaces
whiteboard and group-chat booking, where two people can hold the same room and nobody can check
availability before walking across campus.

This repository is the assessed artefact for **Software Engineering, Assignment 1: Software
Engineering Investigation and Project Planning** (Group Passion). It is also the base for
Assignment 2.

## Author and roles

This is an **individual submission** by **Lei Wen (25307866)**. The roles below are separated
in the process rather than across people; a written review checklist stands in for a second
reviewer, and the pull request records that self-review.

| Role | What it covers |
|---|---|
| Product owner | Scope, backlog, priorities, acceptance criteria, risk register, merge decisions |
| Developer | `server.py`, `storage.py`, `models.py`, `data/rooms.json`, the FR-03 overlap rule, `studyspace/web/` |
| Tester and reviewer | unittest suite, the review checklist applied to every pull request, usability and latency checks |
| Documenter | README and evidence documents, report integration, bundle verification |

## Quick start

Requires Python 3.12. The application uses the standard library only — there is nothing to
install and no build step.

```bash
python -m studyspace --port 8000
```

Open <http://localhost:8000>. Search for a room by date, start time, duration and minimum
capacity, then book it. The SQLite database is created on first run at `data/studyspace.db`
(gitignored).

## Tests

```bash
python -m unittest discover -s tests -v
```

Expected result on the submission release: **20 tests, OK**. Unit tests cover the booking rules
(`tests/test_rules.py`); integration tests drive a live server on an ephemeral port
(`tests/test_api.py`).

## How the workflow works

`main` is always runnable. Every change starts on a short-lived branch, is reviewed by a member
other than its author, passes the test suite, and is merged with a merge commit. Work is tracked
as GitHub issues and pull requests:

- Backlog: [`docs/backlog.md`](docs/backlog.md) (MoSCoW, one row per user story)
- Requirements and acceptance criteria: [`docs/requirements.md`](docs/requirements.md)
- Risk register: [`docs/risk-register.md`](docs/risk-register.md)
- Test plan: [`docs/test-plan.md`](docs/test-plan.md)
- Architecture and design decisions: [`docs/architecture.md`](docs/architecture.md),
  [`docs/decision-log.md`](docs/decision-log.md)

## The trial change (FR-03: reject double bookings)

The workflow was trialled on one small change, followed from tracked requirement to merged code:

| Step | Where |
|---|---|
| Requirement tracked | [Issue #1](https://github.com/ntgi-lan/CISE/issues/1) — FR-03 with acceptance criteria and definition of done |
| Implementation | branch `feature/fr03-double-booking`, commit "feat(booking): reject overlapping bookings for the same room (FR-03)" |
| Tests | commit "test(booking): cover overlap, adjacent-slot and no-side-effect cases" |
| Review | [Pull request #1](https://github.com/ntgi-lan/CISE/pull/1) — review checklist and reviewer comments |
| Merge and release | merge commit on `main`, annotated tag `v0.1.0` |

Evidence files: [`docs/evidence/`](docs/evidence/) (test output, repository state) and
[`docs/workflow-trial.md`](docs/workflow-trial.md) (what happened and what the team learned).

## Assessor access

The repository is public: <https://github.com/ntgi-lan/CISE>.

- Submission release: tag `v0.1.0` (merge commit `da5d6e6`)
- Submission commit: `da5d6e6`
- Read-only clone: `git clone https://github.com/ntgi-lan/CISE.git`

## Reused code and resources

The application is written for this assessment. The only reused resources are the Python
standard library and the seeded room names taken from AUT's WA and WZ room numbering. See
[`docs/decision-log.md`](docs/decision-log.md) for the design decisions and
[`docs/contribution-log.md`](docs/contribution-log.md) for each member's contribution.

## Generative AI use

Generative AI assistance was used to help draft documentation and review code. Every claim in the
report and every test result in `docs/evidence/` was checked against a real run of this
repository. This disclosure follows the course guidance on generative AI use.
