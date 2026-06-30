from .graph import _request


def list_events(token, top=20):
    # ponytail: lists by start time ascending; add a from-now $filter if past
    # events clutter the results.
    params = {
        "$top": top,
        "$orderby": "start/dateTime",
        "$select": "id,subject,start,end,location,organizer",
    }
    resp = _request("GET", "/me/events", token, params=params)
    return resp.json().get("value", [])


def get_event(token, event_id):
    resp = _request("GET", f"/me/events/{event_id}", token)
    return resp.json()


def get_my_address(token):
    resp = _request("GET", "/me", token, params={"$select": "mail,userPrincipalName"})
    data = resp.json()
    return data.get("mail") or data.get("userPrincipalName")


def get_schedule(token, addresses, start, end, timezone, interval=30):
    payload = {
        "schedules": addresses,
        "startTime": {"dateTime": start, "timeZone": timezone},
        "endTime": {"dateTime": end, "timeZone": timezone},
        "availabilityViewInterval": interval,
    }
    resp = _request("POST", "/me/calendar/getSchedule", token, json=payload)
    return resp.json().get("value", [])
