# exchange-ai-connector

An MCP server that lets an AI agent read and send your Microsoft 365 / Outlook
email, with every send gated by your MCP client's confirmation prompt.

## How the human-in-the-loop gate works

`list_emails`, `read_email`, and `read_thread` are read-only and run freely.
`send_email` is the only tool that changes the outside world; it is annotated as
destructive, so your MCP client (e.g. Claude Desktop) shows you the exact
recipients, subject, and body and waits for your approval before it runs. The
draft you review *is* the agent's proposed `send_email` arguments — nothing is
stored half-sent.

## One-time setup

1. Register an app in Microsoft Entra ID:
   - Supported account types: **multitenant + personal Microsoft accounts**.
   - Add a **Mobile and desktop** redirect URI: `http://localhost:8400`.
   - Under **API permissions**, add delegated Microsoft Graph scopes
     `Mail.Read` and `Mail.Send`. On a corporate tenant a tenant admin may need
     to grant consent.
2. Install:
   ```bash
   cd src
   pip install -e .
   ```
3. Export your app's Application (client) ID:
   ```bash
   export EXCHANGE_AI_CLIENT_ID="<your-app-client-id>"
   # optional, to pin to one tenant instead of the multi-tenant default:
   # export EXCHANGE_AI_AUTHORITY="https://login.microsoftonline.com/<tenant-id>"
   ```

## Run

```bash
exchange-ai-connector
```

On first run a browser opens for sign-in and consent; the token is cached in
your OS keychain and refreshed silently afterward.

### Claude Desktop config

```json
{
  "mcpServers": {
    "exchange-ai": {
      "command": "exchange-ai-connector",
      "env": { "EXCHANGE_AI_CLIENT_ID": "<your-app-client-id>" }
    }
  }
}
```

## Manual smoke test

1. Start the server (or restart Claude Desktop with the config above).
2. Ask the agent: "List my latest 5 emails." → confirm `list_emails` returns them.
3. Ask: "Send a test email to myself with subject 'hello'." → the client shows
   the draft; approve it.
4. Check your inbox for the email and confirm a line was appended to
   `~/.exchange-ai-connector/audit.log`.

## Audit log

Every send appends one JSON line (timestamp, recipients, subject) to
`~/.exchange-ai-connector/audit.log`.

## Scope (v1)

Email only. Calendar, a standalone web approval UI, app-only auth, and
multi-account approval are deliberately out of scope; see
`docs/superpowers/specs/2026-06-30-exchange-ai-connector-design.md`.
