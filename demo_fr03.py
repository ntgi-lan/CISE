# -*- coding: utf-8 -*-
"""Live demo for Assignment 1: walk FR-03 through create/409/adjacent/validation.

Runs against the real server. Start it first:
    python -m studyspace --port 8000
then:
    python demo_fr03.py
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
ROOM = "WA-201"
OTHER = "WA-204"
DAY = "2026-11-27"          # a Friday


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


def step(n, label, expect):
    print(f"\n[{n}] {label}   (expect {expect})")


def show(status, body, want):
    ok = "PASS" if status == want else "FAIL"
    mark = "\033[92m" + ok + "\033[0m" if ok == "PASS" else "\033[91m" + ok + "\033[0m"
    print(f"    -> HTTP {status}  {mark}")
    if isinstance(body, dict):
        print("       " + json.dumps(body, ensure_ascii=False)[:220])
    return ok == "PASS"


def main():
    print("=" * 78)
    print("  StudySpace demo — FR-03: reject overlapping bookings")
    print("  server:", BASE, "| room:", ROOM, "| date:", DAY)
    print("=" * 78)
    results = []

    step(1, f"POST /api/bookings  {ROOM} 10:00-11:00 (the first booking)", 201)
    s, b = call("POST", "/api/bookings", {
        "room_id": ROOM, "name": "Demo Student", "email": "demo@autuni.ac.nz",
        "start": f"{DAY}T10:00:00", "end": f"{DAY}T11:00:00"})
    results.append(show(s, b, 201))

    step(2, f"POST /api/bookings  {ROOM} 10:30-11:30 (overlaps the first)", 409)
    s, b = call("POST", "/api/bookings", {
        "room_id": ROOM, "name": "Second Student", "email": "second@autuni.ac.nz",
        "start": f"{DAY}T10:30:00", "end": f"{DAY}T11:30:00"})
    results.append(show(s, b, 409))

    step(3, f"POST /api/bookings  {ROOM} 11:00-12:00 (adjacent, half-open interval)", 201)
    s, b = call("POST", "/api/bookings", {
        "room_id": ROOM, "name": "Third Student", "email": "third@autuni.ac.nz",
        "start": f"{DAY}T11:00:00", "end": f"{DAY}T12:00:00"})
    results.append(show(s, b, 201))

    step(4, f"POST /api/bookings  {OTHER} 10:30-11:30 (different room)", 201)
    s, b = call("POST", "/api/bookings", {
        "room_id": OTHER, "name": "Fourth Student", "email": "fourth@autuni.ac.nz",
        "start": f"{DAY}T10:30:00", "end": f"{DAY}T11:30:00"})
    results.append(show(s, b, 201))

    step(5, f"POST /api/bookings  {ROOM} 10:00-10:15 (15 minutes, too short)", 400)
    s, b = call("POST", "/api/bookings", {
        "room_id": ROOM, "name": "Fifth Student", "email": "fifth@autuni.ac.nz",
        "start": f"{DAY}T10:00:00", "end": f"{DAY}T10:15:00"})
    results.append(show(s, b, 400))

    print("\n" + "-" * 78)
    print(f"  {sum(results)}/{len(results)} checks passed.")
    if all(results):
        print("  The first booking holds the room; the overlap is refused; the adjacent")
        print("  slot and the other room are still bookable. This is the FR-03 behaviour.")
    else:
        print("  Some checks failed — read the status codes above before presenting.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
