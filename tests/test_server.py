from unittest.mock import patch

from exchange_ai_connector import server
from exchange_ai_connector import graph


def test_list_emails_passes_token_and_args():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.graph, "list_messages", return_value=["m"]) as lm:
        out = server.list_emails(folder="inbox", top=3)
    assert out == ["m"]
    assert lm.call_args.args[0] == "TOK"
    assert lm.call_args.kwargs == {"folder": "inbox", "top": 3, "query": None}


def test_send_email_sends_then_audits():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.graph, "send_mail") as sm, \
         patch.object(server.audit, "log_send") as audit_log:
        out = server.send_email(to=["a@b.com"], subject="Hi", body="Body")
    sm.assert_called_once()
    assert sm.call_args.args[0] == "TOK"
    audit_log.assert_called_once_with(["a@b.com"], "Hi", reply_to_id=None)
    assert out == {"status": "sent", "to": ["a@b.com"], "subject": "Hi"}


def test_send_email_skips_audit_when_send_fails():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.graph, "send_mail", side_effect=graph.GraphError("boom")), \
         patch.object(server.audit, "log_send") as audit_log:
        import pytest
        with pytest.raises(graph.GraphError):
            server.send_email(to=["a@b.com"], subject="Hi", body="Body")
    audit_log.assert_not_called()


def test_call_refreshes_token_on_401():
    calls = {"n": 0}

    def flaky(token):
        calls["n"] += 1
        if token == "OLD":
            raise graph.GraphAuthError("401")
        return "ok"

    with patch.object(server.auth, "get_token", side_effect=["OLD", "NEW"]) as gt:
        result = server._call(flaky)
    assert result == "ok"
    assert calls["n"] == 2
    assert gt.call_args_list[1].kwargs == {"force_interactive": True}


def test_list_events_passes_token():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.calendar, "list_events", return_value=["e"]) as le:
        out = server.list_events(top=3)
    assert out == ["e"]
    assert le.call_args.args[0] == "TOK"
    assert le.call_args.kwargs == {"top": 3}


def test_check_availability_defaults_to_self():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.calendar, "get_my_address", return_value="me@x.com") as my, \
         patch.object(server.calendar, "get_schedule", return_value=["sched"]) as gs:
        out = server.check_availability("2026-07-02T14:00:00", "2026-07-02T15:00:00")
    assert out == ["sched"]
    my.assert_called_once()
    assert gs.call_args.args[1] == ["me@x.com"]            # addresses
    assert gs.call_args.args[4] == server.config.timezone   # timezone


def test_check_availability_uses_given_attendees():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.calendar, "get_my_address") as my, \
         patch.object(server.calendar, "get_schedule", return_value=["sched"]) as gs:
        server.check_availability(
            "2026-07-02T14:00:00", "2026-07-02T15:00:00", attendees=["a@b.com"]
        )
    my.assert_not_called()
    assert gs.call_args.args[1] == ["a@b.com"]


def test_create_event_creates_then_audits():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.calendar, "create_event", return_value={"id": "ev9"}) as ce, \
         patch.object(server.audit, "log_create_event") as audit_log:
        out = server.create_event(
            subject="Sync", start="2026-07-02T14:00:00", end="2026-07-02T15:00:00",
            attendees=["a@b.com"],
        )
    ce.assert_called_once()
    assert ce.call_args.args[0] == "TOK"
    assert ce.call_args.args[4] == server.config.timezone
    audit_log.assert_called_once_with("Sync", "2026-07-02T14:00:00", ["a@b.com"])
    assert out == {"status": "created", "subject": "Sync", "start": "2026-07-02T14:00:00", "id": "ev9"}


def test_create_event_skips_audit_when_create_fails():
    with patch.object(server.auth, "get_token", return_value="TOK"), \
         patch.object(server.calendar, "create_event", side_effect=graph.GraphError("boom")), \
         patch.object(server.audit, "log_create_event") as audit_log:
        import pytest
        with pytest.raises(graph.GraphError):
            server.create_event(subject="Sync", start="2026-07-02T14:00:00", end="2026-07-02T15:00:00")
    audit_log.assert_not_called()
