"""Command-line entry point: ``python -m studyspace --port 8000``."""

from __future__ import annotations

import argparse

from . import __version__
from .server import create_server


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the development server."""
    parser = argparse.ArgumentParser(
        prog="studyspace",
        description="Run the StudySpace web application (Python standard library only).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="TCP port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--db",
        default="data/studyspace.db",
        help="SQLite database file (default: data/studyspace.db)",
    )
    parser.add_argument(
        "--rooms",
        default="data/rooms.json",
        help="room catalogue seed file (default: data/rooms.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Start the server and block until interrupted."""
    args = build_parser().parse_args(argv)
    server = create_server(
        host=args.host,
        port=args.port,
        db_path=args.db,
        rooms_path=args.rooms,
    )
    host, port = server.server_address[:2]
    print(f"StudySpace {__version__} listening on http://{host}:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping StudySpace.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
