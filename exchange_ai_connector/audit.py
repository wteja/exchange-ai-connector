import json
import time
from pathlib import Path

AUDIT_PATH = Path.home() / ".exchange-ai-connector" / "audit.log"


def log_send(to, subject, *, reply_to_id=None, path=AUDIT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "to": to,
        "subject": subject,
    }
    if reply_to_id:
        entry["reply_to_id"] = reply_to_id
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_create_event(subject, start, attendees=None, *, path=AUDIT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": "event",
        "subject": subject,
        "start": start,
    }
    if attendees:
        entry["attendees"] = attendees
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
