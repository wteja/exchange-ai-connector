from unittest.mock import patch

import pytest

from exchange_ai_connector import graph


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json


def test_list_messages_happy():
    payload = {"value": [{"id": "1", "subject": "Hi"}]}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)) as req:
        out = graph.list_messages("TOK", folder="inbox", top=5)
    assert out == [{"id": "1", "subject": "Hi"}]
    method, url = req.call_args.args
    assert method == "GET"
    assert url.endswith("/me/mailFolders/inbox/messages")
    assert req.call_args.kwargs["headers"]["Authorization"] == "Bearer TOK"
    assert req.call_args.kwargs["params"]["$top"] == 5


def test_request_raises_on_error():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=403, text="nope")):
        with pytest.raises(graph.GraphError):
            graph.get_message("TOK", "1")


def test_request_401_raises_auth_error():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=401)):
        with pytest.raises(graph.GraphAuthError):
            graph.get_message("TOK", "1")


def test_request_retries_once_on_429():
    responses = [FakeResp(status_code=429, headers={"Retry-After": "0"}),
                 FakeResp(json_data={"id": "1"})]
    with patch.object(graph.httpx, "request", side_effect=responses) as req, \
         patch.object(graph.time, "sleep") as slept:
        out = graph.get_message("TOK", "1")
    assert out == {"id": "1"}
    assert req.call_count == 2
    slept.assert_called_once()


def test_send_mail_uses_sendmail_endpoint():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=202)) as req:
        graph.send_mail("TOK", to=["a@b.com"], subject="Hi", body="Body", cc=["c@d.com"])
    method, url = req.call_args.args
    assert method == "POST"
    assert url.endswith("/me/sendMail")
    body = req.call_args.kwargs["json"]
    assert body["message"]["toRecipients"] == [{"emailAddress": {"address": "a@b.com"}}]
    assert body["message"]["ccRecipients"] == [{"emailAddress": {"address": "c@d.com"}}]
    assert body["saveToSentItems"] is True


def test_send_mail_reply_uses_reply_endpoint():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=202)) as req:
        graph.send_mail("TOK", to=[], subject="", body="Thanks", reply_to_id="msg-9")
    method, url = req.call_args.args
    assert method == "POST"
    assert url.endswith("/me/messages/msg-9/reply")
    assert req.call_args.kwargs["json"]["comment"] == "Thanks"


def test_get_thread_sorts_client_side_and_omits_orderby():
    payload = {"value": [
        {"id": "2", "receivedDateTime": "2026-01-02T00:00:00Z"},
        {"id": "1", "receivedDateTime": "2026-01-01T00:00:00Z"},
    ]}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)) as req:
        out = graph.get_thread("TOK", "conv-1")
    assert [m["id"] for m in out] == ["1", "2"]
    assert "$orderby" not in req.call_args.kwargs["params"]


def test_send_mail_reply_includes_cc():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=202)) as req:
        graph.send_mail("TOK", to=[], subject="", body="Thanks", cc=["c@d.com"], reply_to_id="msg-9")
    body = req.call_args.kwargs["json"]
    assert body["message"]["ccRecipients"] == [{"emailAddress": {"address": "c@d.com"}}]
