from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import audit, auth, graph
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
