from unittest.mock import patch

import pytest

from exchange_ai_connector import calendar, graph


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json


def test_list_events_happy():
    payload = {"value": [{"id": "e1", "subject": "Standup"}]}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)) as req:
        out = calendar.list_events("TOK", top=5)
    assert out == [{"id": "e1", "subject": "Standup"}]
    method, url = req.call_args.args
    assert method == "GET"
    assert url.endswith("/me/events")
    assert req.call_args.kwargs["params"]["$top"] == 5
    assert req.call_args.kwargs["params"]["$orderby"] == "start/dateTime"


def test_list_events_error():
    with patch.object(graph.httpx, "request", return_value=FakeResp(status_code=403, text="no")):
        with pytest.raises(graph.GraphError):
            calendar.list_events("TOK")


def test_get_event_happy():
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data={"id": "e1"})) as req:
        out = calendar.get_event("TOK", "e1")
    assert out == {"id": "e1"}
    method, url = req.call_args.args
    assert method == "GET"
    assert url.endswith("/me/events/e1")


def test_get_my_address_prefers_mail():
    payload = {"mail": "me@x.com", "userPrincipalName": "me@x.onmicrosoft.com"}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)):
        assert calendar.get_my_address("TOK") == "me@x.com"


def test_get_my_address_falls_back_to_upn():
    payload = {"mail": None, "userPrincipalName": "me@x.onmicrosoft.com"}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)):
        assert calendar.get_my_address("TOK") == "me@x.onmicrosoft.com"


def test_get_schedule_builds_payload():
    payload = {"value": [{"scheduleId": "me@x.com", "availabilityView": "00"}]}
    with patch.object(graph.httpx, "request", return_value=FakeResp(json_data=payload)) as req:
        out = calendar.get_schedule(
            "TOK", ["me@x.com"], "2026-07-02T14:00:00", "2026-07-02T15:00:00", "Asia/Bangkok"
        )
    assert out == payload["value"]
    method, url = req.call_args.args
    assert method == "POST"
    assert url.endswith("/me/calendar/getSchedule")
    body = req.call_args.kwargs["json"]
    assert body["schedules"] == ["me@x.com"]
    assert body["startTime"] == {"dateTime": "2026-07-02T14:00:00", "timeZone": "Asia/Bangkok"}
    assert body["endTime"] == {"dateTime": "2026-07-02T15:00:00", "timeZone": "Asia/Bangkok"}
    assert body["availabilityViewInterval"] == 30
