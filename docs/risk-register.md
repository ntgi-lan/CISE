# Risk register — StudySpace

Scores use likelihood (L) × impact (I), each on a 1–5 scale, so the maximum score
is 25. Owners are named members of Group Passion; the iteration review is chaired
by the product owner (Haoguang Wang) and re-scores the register at the start of
each iteration. Review dates fall inside the assignment window.

| ID | Risk | L | I | Score | Response | Owner | Review |
|---|---|---|---|---|---|---|---|
| R1 | **Requirement churn**: the room rules (opening hours, duration, cancellation) change after feedback or after watching real use, forcing rework. | 4 | 3 | 12 | Keep every rule in `studyspace/rules.py` as a pure function with one named test per rule; keep the API contract stable; re-plan at the start of each iteration; change rule behaviour behind the same endpoint. | Haoguang Wang | 11 Nov 2026 |
| R2 | **Team coordination and availability across four members**: competing timetables, unclear ownership of a slice, or one member becoming unavailable stall delivery or duplicate work. | 3 | 4 | 12 | Weekly iteration review chaired by the product owner; every backlog item has a named owner; work split by component and by slice, never by accident; every change reviewed by a member other than its author; each member states availability at the start of the week; keep a time buffer before 13 Nov. | Haoguang Wang | Weekly, 5 Nov and 12 Nov 2026 |
| R3 | **Quality under time pressure**: an untested change breaks an existing rule near the deadline. | 3 | 4 | 12 | Tests are the regression net: every rule has a named unit test, every endpoint an integration test; run the full suite before every commit/merge; no merge without a green suite. | Boyi Jiang | Before every merge |
| R4 | **Data loss or local state corruption**: the SQLite demo database is deleted, corrupted or left dirty in the submission. | 2 | 3 | 6 | Database is created on first run and gitignored; tests use temporary databases; seed data lives in versioned `data/rooms.json`; demo can be reset by deleting the file. | Lei Wen | 4 Nov 2026 |
| R5 | **Privacy / data handling**: storing more personal data than needed, or transferring it externally. | 2 | 4 | 8 | Store only name, email and times; no analytics, no external calls; no secrets in the repository; verify tracked files contain no absolute paths or credentials before submission. | Lei Wen | 12 Nov 2026 |
| R6 | **Assessment environment / offline delivery**: the assessor cannot install packages, or the repository link cannot be opened, so the artefact cannot be demonstrated. | 3 | 5 | 15 | Standard library only; no network at runtime; deliver a self-contained Git bundle and zip with README clone and test commands; verify the bundle by cloning it into a clean temporary directory and running the suite there. | Boyi Jiang | 12 Nov 2026 |

## Notes

- R6 is the highest-impact risk: losing access to the repository would make the
  workflow evidence unverifiable, so the delivery format is tested, not assumed.
- R2 covers coordination rather than a lack of skill: availability across four
  members is the main delivery hazard, so ownership and review pairing are fixed
  in the backlog and checked at the weekly iteration review.
- Risk review is recorded in the contribution log; the register is re-scored at
  the start of each iteration by the product owner with the other members.
