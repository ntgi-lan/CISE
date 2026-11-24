# Risk register — StudySpace

Scores use likelihood (L) × impact (I), each on a 1–5 scale, so the maximum score
is 25. This is an individual submission, so one person owns every response; the review
column records when the register was re-scored, and a written review checklist covers the
step a second reviewer would normally take.

| ID | Risk | L | I | Score | Response | Owner | Review |
|---|---|---|---|---|---|---|---|
| R1 | **Requirement churn**: the room rules (opening hours, duration, cancellation) change after feedback or after watching real use, forcing rework. | 4 | 3 | 12 | Keep every rule in `studyspace/rules.py` as a pure function with one named test per rule; keep the API contract stable; re-plan at the start of each iteration; change rule behaviour behind the same endpoint. | Lei Wen | 11 Nov 2026 |
| R2 | **Single point of failure**: illness, overload or one lost evening stalls the whole submission. | 4 | 4 | 16 | Work Must-have items first; keep a two-day buffer before the deadline; cut scope rather than quality; keep each change small enough to finish in one sitting. | Lei Wen | 12 Nov 2026 |
| R3 | **Quality under time pressure**: an untested change breaks an existing rule near the deadline. | 3 | 4 | 12 | Tests are the regression net: every rule has a named unit test, every endpoint an integration test; run the full suite before every commit/merge; no merge without a green suite. | Lei Wen | Before every merge |
| R4 | **No independent reviewer**: self-review misses what a second pair of eyes would catch. | 4 | 3 | 12 | Apply the written review checklist to every pull request; read the diff in the pull request view, not in the editor; test the boundary cases explicitly. | Lei Wen | Before every merge |
| R5 | **Data loss or local state corruption**: the SQLite demo database is deleted, corrupted or left dirty in the submission. | 2 | 3 | 6 | Database is created on first run and gitignored; tests use temporary databases; seed data lives in versioned `data/rooms.json`; demo can be reset by deleting the file. | Lei Wen | 4 Nov 2026 |
| R6 | **Privacy / data handling**: storing more personal data than needed, or transferring it externally. | 2 | 4 | 8 | Store only name, email and times; no analytics, no external calls; no secrets in the repository; verify tracked files contain no absolute paths or credentials before submission. | Lei Wen | 12 Nov 2026 |
| R7 | **Assessment environment / offline delivery**: the assessor cannot install packages, or the repository link cannot be opened, so the artefact cannot be demonstrated. | 3 | 5 | 15 | Standard library only; no network at runtime; deliver a self-contained Git bundle and zip with README clone and test commands; verify the bundle by cloning it into a clean temporary directory and running the suite there. | Lei Wen | 12 Nov 2026 |

## Notes

- R7 is the highest-impact risk: losing access to the repository would make the
  workflow evidence unverifiable, so the delivery format is tested, not assumed.
- R2 and R4 are the solo-specific risks: one person is both the delivery capacity and the
  review capacity, so both are mitigated by process (buffer and checklist) rather than by
  adding people.
- The register is re-scored at the start of each iteration and the dates are recorded above.
