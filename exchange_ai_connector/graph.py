import time

import httpx

GRAPH = "https://graph.microsoft.com/v1.0"
TIMEOUT = 30.0


class GraphError(Exception):
    """Any non-success response from Microsoft Graph."""


class GraphAuthError(GraphError):
    """HTTP 401 — token rejected. Caller should refresh and retry."""


def _request(method, path, token, *, params=None, json=None):
    url = f"{GRAPH}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.request(method, url, headers=headers, params=params, json=json, timeout=TIMEOUT)
    if resp.status_code == 429:
        # ponytail: single bounded retry on throttle, no retry framework
        time.sleep(float(resp.headers.get("Retry-After", "1")))
        resp = httpx.request(method, url, headers=headers, params=params, json=json, timeout=TIMEOUT)
    if resp.status_code == 401:
        raise GraphAuthError("Microsoft Graph rejected the access token (401).")
    if resp.status_code >= 400:
        raise GraphError(f"Graph {method} {path} failed: {resp.status_code} {resp.text}")
    return resp


def _recipients(addrs):
    return [{"emailAddress": {"address": a}} for a in addrs]


def list_messages(token, folder="inbox", top=20, query=None):
    params = {
        "$top": top,
        "$select": "id,subject,from,receivedDateTime,bodyPreview,conversationId",
    }
    if query:
        params["$search"] = f'"{query}"'
    resp = _request("GET", f"/me/mailFolders/{folder}/messages", token, params=params)
    return resp.json().get("value", [])


def get_message(token, message_id):
    resp = _request("GET", f"/me/messages/{message_id}", token)
    return resp.json()


def get_thread(token, conversation_id):
    params = {
        "$filter": f"conversationId eq '{conversation_id}'",
        "$select": "id,subject,from,receivedDateTime,bodyPreview",
    }
    resp = _request("GET", "/me/messages", token, params=params)
    messages = resp.json().get("value", [])
    return sorted(messages, key=lambda m: m.get("receivedDateTime", ""))


def send_mail(token, to, subject, body, cc=None, reply_to_id=None):
    if reply_to_id:
        payload = {"comment": body}
        message = {}
        if to:
            message["toRecipients"] = _recipients(to)
        if cc:
            message["ccRecipients"] = _recipients(cc)
        if message:
            payload["message"] = message
        _request("POST", f"/me/messages/{reply_to_id}/reply", token, json=payload)
        return
    message = {
        "subject": subject,
        "body": {"contentType": "Text", "content": body},
        "toRecipients": _recipients(to),
    }
    if cc:
        message["ccRecipients"] = _recipients(cc)
    _request("POST", "/me/sendMail", token, json={"message": message, "saveToSentItems": True})
