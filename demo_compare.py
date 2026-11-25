# -*- coding: utf-8 -*-
"""Compare the baseline (no overlap rule) with the fixed version.

Start two servers first:

    fixed   : python -m studyspace --port 8000
    baseline: python -m studyspace --port 8001   (run from the baseline worktree)

Then:

    python demo_compare.py

The script prints the same two bookings against both servers, so the defect in the
first version and the fix are visible side by side.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.request

FIXED = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8001"
ROOM = "WA-201"


def call(base, method, path, payload=None):
    url = base + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, body


def pick_date(base):
    day = dt.date.today() + dt.timedelta(days=7)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    while True:
        d = day.isoformat()
        s, b = call(base, "GET", f"/api/bookings?date={d}")
        rows = b.get("bookings", []) if isinstance(b, dict) else []
        if not rows:
            return d
        day += dt.timedelta(days=7)
        while day.weekday() >= 5:
            day += dt.timedelta(days=1)


def book(base, day, start, end, who):
    return call(base, "POST", "/api/bookings", {
        "room_id": ROOM, "name": who, "email": who + "@autuni.ac.nz",
        "start": f"{day}T{start}:00", "end": f"{day}T{end}:00",
    })


def one(label, base):
    try:
        call(base, "GET", "/api/health")
    except Exception:
        return None, None, None
    day = pick_date(base)
    b1 = book(base, day, "10:00", "11:00", "first")[0]
    b2 = book(base, day, "10:30", "11:30", "second")[0]
    return b1, b2, day


def main():
    fx = one("fixed", FIXED)
    bs = one("baseline", BASE)
    print("=" * 76)
    print("  StudySpace - first version vs fixed version")
    print("=" * 76)
    if fx[0] is None:
        print(f"\nCannot reach the fixed server at {FIXED}")
        print("Start it:  python -m studyspace --port 8000")
        return 2
    if bs[0] is None:
        print(f"\nCannot reach the baseline server at {BASE}")
        print("Start it from the baseline worktree:  python -m studyspace --port 8001")
        return 2

    print(f"\n{'':22s}{'first booking':>14s}{'second booking':>16s}")
    print(f"{'first version':22s}{bs[0]:>14}{bs[1]:>16}   <- double booked")
    print(f"{'fixed version':22s}{fx[0]:>14}{fx[1]:>16}   <- refused")

    print("\nExpected: the first version accepts both overlapping bookings (201, 201);")
    print("the fixed version accepts the first and refuses the second (201, 409).")
    ok = bs[0] == 201 and bs[1] == 201 and fx[0] == 201 and fx[1] == 409
    print("\nComparison holds:", "PASS" if ok else "CHECK THE OUTPUT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
