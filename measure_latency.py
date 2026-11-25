# -*- coding: utf-8 -*-
"""Measure API latency for the Assignment 2 quality scenario.

Starts nothing: run the server first, then run this script.

    python -m studyspace --port 8000
    python measure_latency.py

It measures the room catalogue, the search endpoint and booking creation, and
writes docs/evidence/latency.txt with the environment, inputs and results.
"""
import datetime as dt
import json
import os
import platform
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "evidence", "latency.txt")


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        e.read()
        status = e.code
    return (time.perf_counter() - start) * 1000.0, status


def pct(values, p):
    values = sorted(values)
    k = max(0, min(len(values) - 1, int(round((p / 100.0) * (len(values) - 1)))))
    return values[k]


def summarise(name, samples):
    return {
        "endpoint": name,
        "n": len(samples),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(pct(samples, 95), 2),
        "max_ms": round(max(samples), 2),
        "min_ms": round(min(samples), 2),
    }


def main():
    # pick a free future weekday for the booking runs
    day = dt.date.today() + dt.timedelta(days=14)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)

    catalogue, search, create = [], [], []
    for i in range(N):
        ms, status = call("GET", "/api/rooms")
        catalogue.append(ms)
        ms, status = call("GET", f"/api/rooms?start={day}T10:00:00&end={day}T11:00:00&min_capacity=1")
        search.append(ms)
        # unique (room, slot) pairs: 10 rooms x 16 slots = 160 combinations
        rooms = ["WA-201", "WA-204", "WA-206", "WA-210", "WA-212",
                 "WZ-101", "WZ-103", "WZ-105", "WZ-107", "WZ-109"]
        room = rooms[i % len(rooms)]
        minutes = 8 * 60 + ((i // len(rooms)) % 16) * 30
        start = f"{minutes // 60:02d}:{minutes % 60:02d}:00"
        end_min = minutes + 30
        end = f"{end_min // 60:02d}:{end_min % 60:02d}:00"
        ms, status = call("POST", "/api/bookings", {
            "room_id": room, "name": f"Load {i}", "email": f"load{i}@autuni.ac.nz",
            "start": f"{day}T{start}", "end": f"{day}T{end}",
        })
        create.append(ms)

    rows = [summarise("GET /api/rooms", catalogue),
            summarise("GET /api/rooms?start&end&min_capacity", search),
            summarise("POST /api/bookings", create)]

    lines = [
        "# Latency measurement - StudySpace",
        "",
        f"Recorded: {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"Server: {BASE}",
        f"Python: {platform.python_version()} on {platform.system()} {platform.release()}",
        f"Processor: {platform.processor() or 'unknown'}",
        f"Inputs: {N} sequential requests per endpoint, no concurrency",
        f"Booking window used: {day.isoformat()}, 08:00-16:00, room WZ-109",
        "Procedure: python measure_latency.py (fresh database; server started with "
        "python -m studyspace --port 8000)",
        "",
        "| Endpoint | n | p50 (ms) | p95 (ms) | max (ms) |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['endpoint']} | {r['n']} | {r['p50_ms']} | {r['p95_ms']} | {r['max_ms']} |")
    lines += [
        "",
        "Target from the project plan: p95 under 300 ms.",
        "Result: " + ("target met on every endpoint" if all(r["p95_ms"] < 300 for r in rows)
                       else "target NOT met on at least one endpoint"),
        "",
        "Limitations: sequential requests from one client on one machine; this measures the "
        "single-user latency, not throughput under concurrency.",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
