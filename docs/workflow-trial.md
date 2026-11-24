# Workflow trial — tracking FR-03 from requirement to merged, tested release

Dates: 3–4 November 2026 for the trial work; the evidence was recorded on 5
November 2026. Submission: **individual** (Lei Wen, 25307866). The workflow is GitHub
Flow adapted to a solo submission: every change starts from a tracked backlog item, goes
through a short-lived branch, a written review checklist, an automated check, a merge and a
release tag. The review step is a self-review against that checklist, and this document says
so rather than implying a second reviewer.

| Role | Who | Part in the trial |
|---|---|---|
| Product owner | Lei Wen | Recorded the tracked requirement and acceptance criteria, made the merge decision, applied the release tag |
| Author | Lei Wen | Production change (`rules.check_overlap` and the create-path call) |
| Tester and reviewer | Lei Wen | Wrote the overlap tests and reviewed PR #1 against the checklist |
| Documenter | Lei Wen | Recorded the test output, smoke test and repository state; built and verified the bundle |

## 1. Tracked requirement (3 November)

- Backlog item **US-04** was split by Lei Wen into **US-04a** (create and
  validate a booking) and **US-04b** (reject overlap, FR-03). The split and the gap
  are recorded in [backlog.md](backlog.md#split-of-us-04-recorded-3-november-2026).
- The tracked requirement is [Issue #4](issues/ISSUE-004-fr03-double-booking.md):
  context, acceptance criteria, definition of done and the error contract. It was
  recorded by Lei Wen, taken by Lei Wen, and the acceptance criteria
  were recorded before implementation.
- Requirements and traceability were written at the same time
  ([requirements.md](requirements.md)); the FR-03 row was deliberately marked as
  a gap.

## 2. Branch and commits (4 November)

Branch created from `main` at `c5502cd` (the commit that first made the suite
green with 16 tests, before the overlap rule existed):

```text
git checkout -b feature/fr03-double-booking
```

| Commit | Message | Author | Contents |
|---|---|---|---|
| `e7f073e` | `feat(booking): reject overlapping bookings for the same room (FR-03)` | Lei Wen | `rules.check_overlap` (pure, 409 `overlap`), called from the create path after the daily-limit check and before persistence |
| `481cb06` | `test(booking): cover overlap, adjacent-slot and no-side-effect cases` | Lei Wen | three rule tests and one integration test (`test_rules.OverlapTests`, `test_api.BookingApiTests.test_overlap_returns_409_and_creates_no_record`) |

The branch was created from, and merged back into, `main`; it existed for the
duration of one review and was not pushed anywhere (there is no remote).

**Baseline evidence.** Commit `c5502cd` is a genuine baseline: the create path
contained no overlap check, and two overlapping `POST` requests both returned
201. That was verified with a live server before the feature branch was started;
the feature commits close the gap and the merged application returns 409 for the
same requests (see [evidence/manual-smoke-test.txt](evidence/manual-smoke-test.txt)).

## 3. Review (PR #1)

The review record is [PR-001](pull-requests/PR-001.md). This is an individual
submission, so the review is a **self-review against a written checklist** rather
than a review by a second person; the pull request records the checklist questions
and the answers. The checklist covered correctness (half-open interval, per-room
scope, ordering before persistence), tests (rule and API level, no side effects),
the error contract (409 + `{"error": {"code": "overlap"}}`), documentation and scope
creep. The questions raised during the review — bookings that start before the
requested window, the ordering of the daily-limit check, whether the browser needed
a change — changed the tests where the answer exposed a boundary. The merge was
then made against the checked list.

The automated check was run locally with the same command the CI workflow uses:

```text
python -m unittest discover -s tests -v
Ran 20 tests in 3.851s
OK
```

Verbatim output: [evidence/test-results.txt](evidence/test-results.txt).

## 4. Merge (4 November)

```text
git checkout main
git merge --no-ff feature/fr03-double-booking -m "Merge pull request #1 from feature/fr03-double-booking"
```

Merge commit `9dda54a`, authored by Lei Wen. The merge preserves the branch
in history; the recorded graph (`git log --oneline --graph --decorate`, including
tag `v0.1.0` on the evidence commit) is in `docs/evidence/repo-state.txt`. The
short history is:

```text
9dda54a  Merge pull request #1 from feature/fr03-double-booking
481cb06  test(booking): cover overlap, adjacent-slot and no-side-effect cases
e7f073e  feat(booking): reject overlapping bookings for the same room (FR-03)
c5502cd  test: add unit and integration tests for booking rules and API
0a48708  feat(web): add the single-page room search and booking client
b12b2cf  feat: implement room catalogue, booking rules and JSON API
d6c9910  chore: scaffold StudySpace repository and planning documents
```

## 5. Release tag, recorded state and bundle

The evidence commit (test output, manual smoke test, this record, README and
traceability updates) is tagged **v0.1.0** by Lei Wen.
`docs/evidence/repo-state.txt` is added immediately after the tag in the final
submission commit; it records the tag object, the commit log, `git status`, the
HEAD hash at recording time (the tagged commit) and the absence of remotes, and
`docs/evidence/test-results.txt` holds the real suite output. Lei Wen built
`studyspace.bundle`, cloned it into a temporary directory, verified the tag and
the history, and ran the full suite there.

## What worked

- Writing the acceptance criteria (Given/When/Then) before the code made the
  review objective: 10:30–11:30 must be 409, 11:00–12:00 must be 201. Both are
  asserted at rule level and over HTTP.
- Keeping the rule in `rules.py` meant the whole feature was ~20 lines of
  production code and 100 lines of tests, small enough to review carefully in one
  sitting.
- Splitting the change between author (production code) and tester (tests) meant
  the tests were written against the written acceptance criteria rather than
  against the implementation.
- The no-side-effect test pins the ordering: the overlap rule runs before the
  storage write, so a rejected request cannot leave a record behind.
- The explicit PR checklist caught that the error body had to be verified, not
  just the HTTP status, because the browser needs the `code` to display a useful
  message.

## What the trial changed

- The half-open interval semantics (`start < other_end and other_start < end`)
  are now documented by a test: adjacent slots share the room, which is the
  behaviour students expect and the FR-03 acceptance criterion.
- The README status table and the requirements traceability matrix were updated as
  part of the evidence commit — previously the documentation would have drifted
  from the code after the merge.
- The merge had to be followed by a documentation/evidence commit, so the release
  tag was applied to that commit rather than to the merge commit. The tag
  therefore points at the commit that contains the recorded evidence, and the
  merge commit is its second parent.
- The review conversation made the ordering of daily-limit versus overlap
  explicit; the implementation keeps the daily limit first so the more specific
  hourly cap is reported before the room conflict.

## Lessons carried into Iteration 2

1. Budget documentation and evidence updates into the definition of done; they
   are part of the change, not follow-up work.
2. Keep each slice to one rule and one test group so the review checklist stays
   meaningful.
3. Separate author and reviewer even when the change is small; the tester's
   questions changed the tests before the merge.
4. Run the full suite before every commit, not just before the merge.
5. Record the real command output immediately after the run; never retype it.
