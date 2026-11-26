"""Shared fixtures for the StudySpace test suite.

The integration tests run the real ``ThreadingHTTPServer`` on an ephemeral port
against a throwaway SQLite database, so the suite exercises the same code path as
the running application. The clock is injected with a fixed Wednesday so the
test data is deterministic regardless of when the suite runs.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from studyspace.server import create_server

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOMS_PATH = REPO_ROOT / "data" / "rooms.json"

# Wednesday 4 November 2026, 08:00 (before the weekday opening time).
FIXED_NOW = datetime(2026, 11, 4, 8, 0)
BOOKING_DAY = "2026-11-05"  # Thursday, one day after FIXED_NOW


def booking_payload(
    *,
    room_id: str = "WA-201",
    start: str = f"{BOOKING_DAY}T10:00:00",
    end: str = f"{BOOKING_DAY}T11:00:00",
    name: str = "Alex Student",
    email: str = "alex.student@autuni.ac.nz",
) -> dict[str, str]:
    """Build a valid booking payload; individual tests override one field."""
    return {
        "room_id": room_id,
        "name": name,
        "email": email,
        "start": start,
        "end": end,
    }


class ServerFixture:
    """Run the application server on an ephemeral port for one test."""

    def __init__(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="studyspace-test-"
        )
        database_path = Path(self._temporary_directory.name) / "studyspace.db"
        self.server = create_server(
            host="127.0.0.1",
            port=0,
            db_path=database_path,
            rooms_path=ROOMS_PATH,
            rooms_extra_path=Path(database_path).with_name("rooms_added.json"),
            clock=lambda: FIXED_NOW,
        )
        host, port = self.server.server_address[:2]
        self.base_url = f"http://{host}:{port}"
        self._thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        """Stop the server and remove the temporary database directory."""
        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=5)
        self._temporary_directory.cleanup()

    def request(
        self, method: str, path: str, payload: object | None = None
    ) -> tuple[int, dict[str, object] | None]:
        """Send a JSON request and return ``(status, decoded_body)``."""
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"} if body else {},
        )
        return self._perform(request)

    def request_raw(
        self, method: str, path: str, body: bytes
    ) -> tuple[int, dict[str, object] | None]:
        """Send a raw body, used to test malformed JSON handling."""
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        return self._perform(request)

    @staticmethod
    def _perform(
        request: urllib.request.Request,
    ) -> tuple[int, dict[str, object] | None]:
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read()
                return response.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as error:
            raw = error.read()
            return error.code, (json.loads(raw) if raw else None)


class ServerTestCase(unittest.TestCase):
    """Base class that gives every test a fresh server and database."""

    server_fixture: ServerFixture

    def setUp(self) -> None:
        self.api = ServerFixture()
        self.addCleanup(self.api.close)
