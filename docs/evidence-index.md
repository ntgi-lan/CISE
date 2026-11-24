# Evidence index — StudySpace (Group Passion)

Map from assessment criteria and claims to repository artefacts and the commits
that contain them. Short hashes refer to this repository's history; the same
values are recorded in `docs/evidence/repo-state.txt`.

| Assessment criterion | Claim / evidence | Artefact | Commit |
|---|---|---|---|
| Problem definition and scope (15) | Problem, value, stakeholders, scope in/out, constraints, three engineering issues | `README.md`; report §1 (outside this repo); scope statement in `docs/requirements.md` ("Out of scope") | the recorded commit; final versions in the tagged evidence commit |
| Comparison and justification of approaches (30) | Technical approach and decisions: stdlib only, threading HTTP server, SQLite, pure rules, Git bundle delivery | `docs/decision-log.md` (DL-001–DL-006 with owners), `docs/architecture.md` | the recorded commit; final versions in the tagged evidence commit |
| Workflow setup and application evidence (30) | Team roles, ownership and review pairing | `README.md` ("Team"), `docs/contribution-log.md`, `docs/backlog.md` (owner column) | the recorded commit; team sections in the tagged evidence commit |
| | Backlog with MoSCoW, owners and the split of US-04 | `docs/backlog.md` | the recorded commit; completed status in the tagged evidence commit |
| | Tracked requirement with acceptance criteria and definition of done | `docs/issues/ISSUE-001-fr03-double-booking.md` | the recorded commit (opened by Wang); resolution in the tagged evidence commit |
| | Short-lived branch with two focused commits (author Zhang, tests Jiang) | commits the recorded commit and the recorded commit on `feature/fr03-double-booking` | the recorded commit, the recorded commit |
| | Reviewed change by a member other than the author: summary, checks, checklist, review conversation, merge decision | `docs/pull-requests/PR-002.md` | the tagged evidence commit |
| | Merge commit with `--no-ff`, approved by Wang | the recorded commit | the recorded commit |
| | Release tag applied by Wang | annotated tag `v0.1.0` applied by Haoguang Wang; the tag object hash and target are recorded in `docs/evidence/repo-state.txt` | `v0.1.0` |
| | Workflow narrative, what worked, what the trial changed, lessons | `docs/workflow-trial.md` | the tagged evidence commit |
| | Verification that it works: live HTTP smoke test (health, create, overlap 409, cancel 204) | `docs/evidence/manual-smoke-test.txt` | the tagged evidence commit |
| | Real automated test output (20 tests, all passing) | `docs/evidence/test-results.txt` | the tagged evidence commit |
| | Repository state: graph, status, tags, HEAD hash, no remotes | `docs/evidence/repo-state.txt` | submission commit (the tip of `main`; records HEAD at the tagged evidence commit) |
| Iteration planning and risk (15) | Two iterations, acceptance criteria AC1–AC6, responsibilities, risks, evaluation measures | `docs/backlog.md`; report §3; `docs/risk-register.md` (owners Wang/Wang/Jiang/Wen/Wen/Jiang) | the recorded commit; owner column in the tagged evidence commit |
| | Testable requirements and traceability matrix (requirement → backlog → file → test) | `docs/requirements.md` | the recorded commit; final status in the tagged evidence commit |
| | NFR-02 performance and NFR-03 usability checks | `docs/test-plan.md` (manual checks, recorded in report) | the recorded commit |
| Communication and referencing (10) | Reproducible setup and test instructions for an assessor | `README.md` ("Quick start", "Tests", "Assessor access") | the recorded commit; final version in the tagged evidence commit |
| | Contribution statement and effort log for four members; AI-use disclosure | `docs/contribution-log.md`; report §5 and Table 4 | the recorded commit (final log) |
| | Offline delivery of the full history | `studyspace.bundle` in the submission package; clone instructions in `README.md` | bundle created after `v0.1.0` |

## How to reproduce the evidence

From a clone of the bundle:

```bash
git log --oneline --graph --decorate
git show --stat the recorded commit
git show --stat the recorded commit
git show v0.1.0
python -m unittest discover -s tests -v
```

Expected: `Ran 20 tests … OK`; the graph shows the feature branch merged at
the recorded commit; the tag `v0.1.0` points at the evidence commit and contains the
evidence files listed above.

## Notes

- The repository has no hosted Git URL by design (the team has no account and no
  network); the bundle is the delivery format and is verified by cloning it into a
  clean temporary directory and running the suite there.
- Test output and smoke-test output are real command transcripts; they are never
  hand-edited.
- The author/reviewer pairing is recorded in the pull-request document and in the
  workflow narrative: Jiawei Zhang authored the production change, Boyi Jiang wrote
  the tests and reviewed the PR, Haoguang Wang approved and performed the merge and
  applied the tag, Lei Wen recorded the evidence and verified the bundle.
