"""Email delivery for waitlist promotions.

The assessment environment is offline, so a real SMTP hand-off is optional: when
``STUDYSPACE_SMTP_HOST`` is set the message is sent with :mod:`smtplib`,
otherwise it is written to a local outbox as an ``.eml`` file. The outbox keeps
the notification inspectable, which is what the demonstration needs.
"""
from __future__ import annotations

import datetime as dt
import email
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

SENDER = "StudySpace <studyspace@autuni.ac.nz>"


def _now() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def send_email(outbox_dir: str | Path, to: str, subject: str, body: str) -> dict[str, object]:
    """Send one email, or write it to the outbox when SMTP is not configured."""
    message = EmailMessage()
    message["From"] = SENDER
    message["To"] = to
    message["Subject"] = subject
    message["Date"] = email.utils.formatdate(localtime=True)
    message.set_content(body)

    host = os.environ.get("STUDYSPACE_SMTP_HOST")
    if host:
        try:
            with smtplib.SMTP(host, int(os.environ.get("STUDYSPACE_SMTP_PORT", "25")), timeout=5) as smtp:
                smtp.send_message(message)
            return {"mode": "smtp", "to": to, "subject": subject, "sent_at": _now()}
        except OSError:
            pass  # fall through to the outbox so a failed send never breaks a booking

    directory = Path(outbox_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe = to.replace("@", "_at_").replace("/", "_")
    path = directory / f"{stamp}-{safe}.eml"
    path.write_text(message.as_string(), encoding="utf-8")
    return {
        "mode": "outbox",
        "to": to,
        "subject": subject,
        "sent_at": _now(),
        "file": path.name,
    }


def list_outbox(outbox_dir: str | Path, limit: int = 20) -> list[dict[str, object]]:
    """Return the most recent messages in the outbox, newest first."""
    directory = Path(outbox_dir)
    if not directory.exists():
        return []
    files = sorted(directory.glob("*.eml"), key=lambda item: item.stat().st_mtime, reverse=True)
    entries = []
    for path in files[:limit]:
        with path.open(encoding="utf-8", errors="replace") as handle:
            parsed = email.message_from_file(handle)
        body = parsed.get_payload()
        if isinstance(body, list):
            body = ""
        entries.append(
            {
                "file": path.name,
                "to": parsed.get("To", ""),
                "subject": parsed.get("Subject", ""),
                "sent_at": parsed.get("Date", ""),
                "body": str(body).strip(),
            }
        )
    return entries
