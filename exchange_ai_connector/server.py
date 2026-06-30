from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import audit, auth, calendar, graph
from .config import Config

config = Config.from_env()
mcp = FastMCP("exchange-ai-connector")

READ_ONLY = ToolAnnotations(readOnlyHint=True)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def _call(fn):
    """Run fn(token); on a 401, force interactive re-auth once and retry."""
    try:
        return fn(auth.get_token(config))
    except graph.GraphAuthError:
        return fn(auth.get_token(config, force_interactive=True))


@mcp.tool(annotations=READ_ONLY)
def list_emails(folder: str = "inbox", top: int = 20, query: str | None = None) -> list[dict]:
    """List messages in a mail folder. Read-only."""
    return _call(lambda t: graph.list_messages(t, folder=folder, top=top, query=query))


@mcp.tool(annotations=READ_ONLY)
def read_email(message_id: str) -> dict:
    """Read one message in full. Read-only."""
    return _call(lambda t: graph.get_message(t, message_id))


@mcp.tool(annotations=READ_ONLY)
def read_thread(conversation_id: str) -> list[dict]:
    """Read all messages in a conversation, oldest first. Read-only."""
    return _call(lambda t: graph.get_thread(t, conversation_id))


@mcp.tool(annotations=DESTRUCTIVE)
def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    reply_to_id: str | None = None,
) -> dict:
    """Send or reply to an email. IRREVERSIBLE — the client must confirm before allowing."""
    _call(lambda t: graph.send_mail(
        t, to=to, subject=subject, body=body, cc=cc, reply_to_id=reply_to_id
    ))
    audit.log_send(to, subject, reply_to_id=reply_to_id)
    return {"status": "sent", "to": to, "subject": subject}


@mcp.tool(annotations=READ_ONLY)
def list_events(top: int = 20) -> list[dict]:
    """List upcoming calendar events, soonest first. Read-only."""
    return _call(lambda t: calendar.list_events(t, top=top))


@mcp.tool(annotations=READ_ONLY)
def read_event(event_id: str) -> dict:
    """Read one calendar event in full. Read-only."""
    return _call(lambda t: calendar.get_event(t, event_id))


@mcp.tool(annotations=READ_ONLY)
def check_availability(
    start: str,
    end: str,
    attendees: list[str] | None = None,
    interval: int = 30,
) -> list[dict]:
    """Free/busy over a window. Times are naive local, e.g. '2026-07-02T14:00:00'.
    attendees defaults to just you. Read-only."""
    def run(t):
        addresses = attendees if attendees else [calendar.get_my_address(t)]
        return calendar.get_schedule(t, addresses, start, end, config.timezone, interval=interval)
    return _call(run)


@mcp.tool(annotations=DESTRUCTIVE)
def create_event(
    subject: str,
    start: str,
    end: str,
    body: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
) -> dict:
    """Create a calendar event; emails invites to attendees. Times are naive local,
    e.g. '2026-07-02T14:00:00'. IRREVERSIBLE — the client must confirm before allowing."""
    event = _call(lambda t: calendar.create_event(
        t, subject, start, end, config.timezone,
        body=body, location=location, attendees=attendees,
    ))
    audit.log_create_event(subject, start, attendees)
    return {"status": "created", "subject": subject, "start": start, "id": event.get("id")}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
