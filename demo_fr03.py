# -*- coding: utf-8 -*-
"""Live demo for Assignment 1: walk the FR-03 acceptance criteria.

Start the server first:
    python -m studyspace --port 8000

Then, in another terminal:
    python demo_fr03.py

The script picks a free future date automatically, so it can be run more than
once without a stale booking blocking the first step. It prints plain PASS/FAIL
lines (no colour codes) so it is safe on a projector.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
ROOM = "WA-201"
OTHER = "WA-204"


def call(method, path, payload=None):
    url = BASE + path
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


def pick_date():
    """A weekday at least a week ahead, so the demo never collides with old data."""
    day = dt.date.today() + dt.timedelta(days=7)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    return day.isoformat()


def book(room, start, end, who):
    day = DAY
    return call("POST", "/api/bookings", {
        "room_id": room, "name": who, "email": who.replace(" ", ".").lower() + "@autuni.ac.nz",
        "start": f"{day}T{start}:00", "end": f"{day}T{end}:00",
    })


def check(n, label, status, body, want):
    ok = status == want
    print(f"[{n}] {label}")
    print(f"    expected HTTP {want}, got HTTP {status}   {'PASS' if ok else 'FAIL'}")
    if isinstance(body, dict) and "error" in body:
        print(f"    error code: {body['error'].get('code')}")
    return ok


DAY = pick_date()


def main():
    global DAY
    print("=" * 78)
    print("  StudySpace demo - FR-03: reject overlapping bookings")
    print(f"  server: {BASE} | room: {ROOM}")
    print("=" * 78)

    try:
        status, _ = call("GET", "/api/health")
    except Exception as e:
        print(f"\nCannot reach the server at {BASE}.")
        print("Start it first:  python -m studyspace --port 8000")
        print(f"({type(e).__name__}: {e})")
        return 2
    if status != 200:
        print(f"\nServer is running but /api/health returned {status}.")
        return 2

    results = []

    # If the chosen date already has bookings from an earlier run, move a week on.
    for _ in range(8):
        s, b = call("GET", f"/api/bookings?date={DAY}")
        rows = b.get("bookings", []) if isinstance(b, dict) else []
        if not rows:
            break
        DAY = (dt.date.fromisoformat(DAY) + dt.timedelta(days=7)).isoformat()
        while dt.date.fromisoformat(DAY).weekday() >= 5:
            DAY = (dt.date.fromisoformat(DAY) + dt.timedelta(days=1)).isoformat()
    print(f"  demo date: {DAY}")

    print("\n[1] First booking, 10:00-11:00")
    s, b = book(ROOM, "10:00", "11:00", "Demo Student")
    results.append(check(1, "create the first booking", s, b, 201))

    print("\n[2] Overlapping booking, 10:30-11:30 (must be refused)")
    s, b = book(ROOM, "10:30", "11:30", "Second Student")
    results.append(check(2, "reject the overlap with 409 and error code 'overlap'", s, b, 409))

    print("\n[3] Adjacent booking, 11:00-12:00 (half-open interval: must be allowed)")
    s, b = book(ROOM, "11:00", "12:00", "Third Student")
    results.append(check(3, "allow the adjacent slot", s, b, 201))

    print("\n[4] Same time, different room (must be allowed)")
    s, b = book(OTHER, "10:30", "11:30", "Fourth Student")
    results.append(check(4, "allow another room", s, b, 201))

    print("\n[5] 15-minute booking (below the 30-minute minimum)")
    s, b = book(ROOM, "13:00", "13:15", "Fifth Student")
    results.append(check(5, "reject a too-short booking with 400", s, b, 400))

    print("\n" + "-" * 78)
    print(f"  {sum(results)}/{len(results)} checks passed.")
    if all(results):
        print("  The first booking holds the room; the overlap is refused; the adjacent")
        print("  slot and the other room are still bookable.")
    else:
        print("  Some checks failed - read the status codes above before presenting.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
