# Demo guide

A two-minute live walkthrough of the FR-03 rule. The same five checks are recorded in
`docs/evidence/test-results.txt` and in the assignment presentation (backup slide).

## Start the server

```bash
python -m studyspace --port 8000
```

Open <http://localhost:8000> to see the single-page client.

## Run the demo

In a second terminal, from the repository root:

```bash
python demo_fr03.py
```

The script picks a free future weekday automatically, so it can be run more than once
without a stale booking blocking the first step.

## What the five checks show

| # | Request | Expected | Why it matters |
|---|---|---|---|
| 1 | Book WA-201 10:00-11:00 | 201 | the room is now held by one record |
| 2 | Book WA-201 10:30-11:30 | 409, `overlap` | the double booking is refused |
| 3 | Book WA-201 11:00-12:00 | 201 | adjacent slots do not overlap (half-open interval) |
| 4 | Book WA-204 10:30-11:30 | 201 | another room is unaffected |
| 5 | Book WA-201 for 15 minutes | 400, `duration` | the duration rule also holds |

Expected final line: `5/5 checks passed.`

## If the demo cannot run

1. Show the backup slide in the presentation (recorded terminal output).
2. Show `docs/evidence/test-results.txt` (20 tests, OK).
3. Fall back to the timeline diagram on the half-open interval slide.

## Troubleshooting

- `Address already in use`: use another port (`--port 8001`) and pass the base URL:
  `python demo_fr03.py http://127.0.0.1:8001`
- `Could not connect`: start the server first; the script prints the command.
- A failed check after repeated runs: delete `data/studyspace.db` and restart the server.
