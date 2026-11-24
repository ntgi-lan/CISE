# Evidence index - StudySpace (Lei Wen, 25307866)

Map from assessment criteria and claims to repository artefacts and the commits
that contain them. Short hashes refer to this repository's history; the same
values are recorded in `docs/evidence/repo-state.txt`.

| Assessment criterion | Claim / evidence | Artefact | Commit |
|---|---|---|---|
| Problem definition and scope (15) | Problem, value, stakeholders, scope in/out, constraints, three engineering issues | `README.md`; report §1 (outside this repo); scope statement in `docs/requirements.md` ("Out of scope") | `d6c9910`; final versions in the tagged evidence commit |
| Comparison and justification of approaches (30) | Technical approach and decisions: stdlib only, threading HTTP server, SQLite, pure rules, Git bundle delivery | `docs/decision-log.md` (DL-001–DL-006 with owners), `docs/architecture.md` | `d6c9910`; final versions in the tagged evidence commit |
| Workflow setup and application evidence (30) | Roles held by one person, ownership and the self-review checklist | `README.md` ("Author and roles"), `docs/contribution-log.md`, `docs/backlog.md` (owner column) | `d6c9910`; role sections in the tagged evidence commit |
| | Backlog with MoSCoW, owners and the split of US-04 | `docs/backlog.md` | `d6c9910`; completed status in the tagged evidence commit |
| | Tracked requirement with acceptance criteria and definition of done | `docs/issues/ISSUE-004-fr03-double-booking.md` | `d6c9910` (opened by Wang); resolution in the tagged evidence commit |
| | Short-lived branch with two focused commits (author Zhang, tests Jiang) | commits `e7f073e` and `481cb06` on `feature/fr03-double-booking` | `e7f073e`, `481cb06` |
| | Reviewed change by a member other than the author: summary, checks, checklist, review conversation, merge decision | `docs/pull-requests/PR-001.md` | the tagged evidence commit |
| | Merge commit with `--no-ff`, approved by Wang | `9dda54a` | `9dda54a` |
| | Release tag applied by Wang | annotated tag `v0.1.0` applied by Lei Wen; the tag object hash and target are recorded in `docs/evidence/repo-state.txt` | `v0.1.0` |
| | Workflow narrative, what worked, what the trial changed, lessons | `docs/workflow-trial.md` | the tagged evidence commit |
| | Verification that it works: live HTTP smoke test (health, create, overlap 409, cancel 204) | `docs/evidence/manual-smoke-test.txt` | the tagged evidence commit |
| | Real automated test output (20 tests, all passing) | `docs/evidence/test-results.txt` | the tagged evidence commit |
| | Repository state: graph, status, tags, HEAD hash, no remotes | `docs/evidence/repo-state.txt` | submission commit (the tip of `main`; records HEAD at the tagged evidence commit) |
| Iteration planning and risk (15) | Two iterations, acceptance criteria AC1–AC6, responsibilities, risks, evaluation measures | `docs/backlog.md`; report §3; `docs/risk-register.md` (owners Wang/Wang/Jiang/Wen/Wen/Jiang) | `d6c9910`; owner column in the tagged evidence commit |
| | Testable requirements and traceability matrix (requirement → backlog → file → test) | `docs/requirements.md` | `d6c9910`; final status in the tagged evidence commit |
| | NFR-02 performance and NFR-03 usability checks | `docs/test-plan.md` (manual checks, recorded in report) | `d6c9910` |
| Communication and referencing (10) | Reproducible setup and test instructions for an assessor | `README.md` ("Quick start", "Tests", "Assessor access") | `d6c9910`; final version in the tagged evidence commit |
| | Contribution statement and effort log for the individual submission | `docs/contribution-log.md`; report §5 and Table 4 | `d6c9910` (final log) |
| | Offline delivery of the full history | `studyspace.bundle` in the submission package; clone instructions in `README.md` | bundle created after `v0.1.0` |

## How to reproduce the evidence

From a clone of the bundle:

```bash
git log --oneline --graph --decorate
git show --stat e7f073e
git show --stat 481cb06
git show v0.1.0
python -m unittest discover -s tests -v
```

Expected: `Ran 20 tests … OK`; the graph shows the feature branch merged at
`9dda54a`; the tag `v0.1.0` points at the evidence commit and contains the
evidence files listed above.

## Notes

- The repository has no hosted Git URL by design (the team has no account and no
  network); the bundle is the delivery format and is verified by cloning it into a
  clean temporary directory and running the suite there.
- Test output and smoke-test output are real command transcripts; they are never
  hand-edited.
- The author/reviewer pairing is recorded in the pull-request document and in the
  workflow narrative: Lei Wen authored the production change, Lei Wen wrote
  the tests and reviewed the PR, Lei Wen approved and performed the merge and
  applied the tag, Lei Wen recorded the evidence and verified the bundle.
