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
