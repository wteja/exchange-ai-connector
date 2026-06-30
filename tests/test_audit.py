import json

from exchange_ai_connector import audit


def test_log_send_appends_one_json_line(tmp_path):
    log = tmp_path / "audit.log"
    audit.log_send(["a@b.com"], "Hello", path=log)
    audit.log_send(["c@d.com"], "Second", path=log)
    lines = log.read_text().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["to"] == ["a@b.com"]
    assert first["subject"] == "Hello"
    assert "ts" in first


def test_log_send_creates_parent_dir(tmp_path):
    log = tmp_path / "nested" / "audit.log"
    audit.log_send(["a@b.com"], "Hi", path=log)
    assert log.exists()


def test_log_send_records_reply_to_id(tmp_path):
    log = tmp_path / "audit.log"
    audit.log_send([], "", reply_to_id="msg-42", path=log)
    entry = json.loads(log.read_text().splitlines()[0])
    assert entry["reply_to_id"] == "msg-42"


def test_log_create_event_writes_event_line(tmp_path):
    p = tmp_path / "audit.log"
    audit.log_create_event("Sync", "2026-07-02T14:00:00", attendees=["a@b.com"], path=p)
    line = json.loads(p.read_text().strip())
    assert line["kind"] == "event"
    assert line["subject"] == "Sync"
    assert line["start"] == "2026-07-02T14:00:00"
    assert line["attendees"] == ["a@b.com"]
    assert "ts" in line


def test_log_create_event_omits_empty_attendees(tmp_path):
    p = tmp_path / "audit.log"
    audit.log_create_event("Solo", "2026-07-02T14:00:00", path=p)
    line = json.loads(p.read_text().strip())
    assert "attendees" not in line
