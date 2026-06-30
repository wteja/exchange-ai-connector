# exchange-ai-connector

An MCP server that lets an AI agent read and act on your Microsoft 365 / Outlook
**email and calendar**, with every state-changing action (sending mail, creating
an event) gated by your MCP client's confirmation prompt.

[On PyPI](https://pypi.org/project/exchange-ai-connector/): `uvx exchange-ai-connector`
or `pipx install exchange-ai-connector`. See [Setup](#setup).

## Tools

| Tool                 | Kind         | What it does                                           |
|----------------------|--------------|--------------------------------------------------------|
| `list_emails`        | read-only    | List messages in a folder (default inbox)              |
| `read_email`         | read-only    | Read one message in full                               |
| `read_thread`        | read-only    | Read a whole conversation, oldest → newest             |
| `send_email`         | **gated**    | Send or reply — client confirms first                  |
| `list_events`        | read-only    | List upcoming calendar events                          |
| `read_event`         | read-only    | Read one event in full                                 |
| `check_availability` | read-only    | Free/busy for you (+ others) — *work/school only*      |
| `create_event`       | **gated**    | Create an event, optionally inviting attendees         |

## How the human-in-the-loop gate works

The read-only tools run freely. The two **gated** tools (`send_email`,
`create_event`) are the only ones that change the outside world; they are
annotated as destructive, so your MCP client (e.g. Claude Desktop) shows you the
exact arguments — recipients, subject, body / event details — and waits for your
approval before running. The draft you review *is* the agent's proposed
arguments; nothing is stored half-sent. Reject and it vanishes.

## Account-type support

| Account type                          | Email | Calendar read/create | `check_availability` |
|---------------------------------------|:-----:|:--------------------:|:--------------------:|
| Work / school (Microsoft 365)         |   ✅  |          ✅          |          ✅          |
| Personal (outlook.com / hotmail)      |   ✅  |          ✅          |          ❌¹         |

¹ Graph's `getSchedule` (free/busy) is not available on personal Microsoft
accounts. `check_availability` returns a readable error there; every other tool
works.

---

## Setup

### 1. Register an app in Microsoft Entra ID

1. Go to **https://entra.microsoft.com** → **Identity → Applications → App
   registrations** → **New registration**.
2. **Name:** anything (e.g. `exchange-ai-connector`).
3. **Supported account types:** *Accounts in any organizational directory
   (multitenant) and personal Microsoft accounts*.
4. **Redirect URI:** platform **Public client/native (mobile & desktop)**, value
   `http://localhost:8400`.
5. Click **Register**, then copy the **Application (client) ID** from the
   overview page — you'll need it below.

### 2. Add Microsoft Graph permissions

1. In your app → **API permissions** → **Add a permission** → **Microsoft
   Graph** → **Delegated permissions**.
2. Add: **`Mail.Read`**, **`Mail.Send`**, **`Calendars.ReadWrite`**.
3. **Personal account:** nothing more — you consent in the browser on first run.
   **Work/school account:** a tenant admin may need to click **Grant admin
   consent**.

> Adding `Calendars.ReadWrite` later (e.g. after using email-only) triggers a
> one-time browser re-consent on the next run. See *Re-consent* below.

### 3. Install

Pick one:

**`uvx` (recommended — no clone, no venv).** Requires [uv](https://docs.astral.sh/uv/).
Nothing to install ahead of time — `uvx` fetches and runs the command in a
throwaway environment. It's used directly in the Claude Desktop config below, so
you can skip straight to that section.

**`pipx`** — puts the `exchange-ai-connector` command on your PATH globally:

```bash
pipx install exchange-ai-connector
# or an unreleased version straight from source:
pipx install git+https://github.com/wteja/exchange-ai-connector
```

**From source (for development):**

```bash
git clone https://github.com/wteja/exchange-ai-connector
cd exchange-ai-connector
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
which exchange-ai-connector   # note this path for the Claude Desktop config
```

### 4. Configure environment

```bash
export EXCHANGE_AI_CLIENT_ID="<your-app-client-id>"

# optional — pin to one tenant instead of the multi-tenant default:
# export EXCHANGE_AI_AUTHORITY="https://login.microsoftonline.com/<tenant-id>"

# optional — override the auto-detected timezone (default: /etc/localtime, else UTC):
# export EXCHANGE_AI_TIMEZONE="Asia/Bangkok"
```

`EXCHANGE_AI_CLIENT_ID` is required; the other two are optional.

---

## Claude Desktop setup

Edit (on macOS) `~/Library/Application Support/Claude/claude_desktop_config.json`
and add an `exchange-ai` server under `mcpServers`. The `uvx` form needs no clone
or venv — it fetches `exchange-ai-connector` from PyPI and runs it:

```json
{
  "mcpServers": {
    "exchange-ai": {
      "command": "/opt/homebrew/bin/uvx",
      "args": ["exchange-ai-connector"],
      "env": {
        "EXCHANGE_AI_CLIENT_ID": "<your-app-client-id>",
        "EXCHANGE_AI_TIMEZONE": "Asia/Bangkok"
      }
    }
  }
}
```

> **Use the absolute path to `uvx`** (`which uvx` — e.g.
> `/opt/homebrew/bin/uvx` on Apple-Silicon Homebrew). Claude Desktop is a GUI app
> and does **not** inherit your shell's `PATH`, so a bare `"uvx"` won't be found.

Useful variants for the `args`:

- **Pin a version** (reproducible; uses uv's cache without re-resolving — handy if
  your network can't always reach PyPI): `["exchange-ai-connector@0.2.0"]`
- **Run an unreleased version from GitHub:**
  `["--from", "git+https://github.com/wteja/exchange-ai-connector", "exchange-ai-connector"]`

If you installed **from source into a venv** instead, point `command` at the
binary's absolute path (same PATH reason as above):

```json
"command": "/ABSOLUTE/PATH/TO/.venv/bin/exchange-ai-connector"
```

### Claude Code (`.mcp.json`)

For Claude Code, put the same server under `mcpServers` in a `.mcp.json` at your
project root (Claude Code expands `${VAR}` from your environment):

```json
{
  "mcpServers": {
    "exchange-ai": {
      "command": "uvx",
      "args": ["exchange-ai-connector"],
      "env": {
        "EXCHANGE_AI_CLIENT_ID": "${EXCHANGE_AI_CLIENT_ID}",
        "EXCHANGE_AI_TIMEZONE": "Asia/Bangkok"
      }
    }
  }
}
```

`EXCHANGE_AI_TIMEZONE` is optional — omit it to auto-detect from the system
(`/etc/localtime`, falling back to UTC). `command` can be a bare `uvx` here
because Claude Code runs from your shell and inherits its `PATH` (unlike the
Claude Desktop GUI, which needs the absolute path).

Then **fully quit** Claude Desktop (Cmd+Q) and reopen it. The `exchange-ai`
server and its tools should appear in the tools/connector list.

On the **first tool call** a browser opens for sign-in and consent; the token is
cached in your OS keychain and refreshed silently afterward.

**Suggested approvals:** allow the read-only tools (`list_emails`, `read_email`,
`read_thread`, `list_events`, `read_event`, `check_availability`) to run without
asking, but leave `send_email` and `create_event` on *ask every time* — that's
the human-in-the-loop gate doing its job.

### Run standalone (without a client)

```bash
exchange-ai-connector
```

It's a stdio MCP server, so it waits silently for a client to connect — there's
no interactive output. This is mainly useful for confirming it starts.

---

## Example usage (sample prompts)

Once it's wired into Claude Desktop, drive it in plain language. Examples:

**Reading email**
- "List my latest 10 emails."
- "Show me unread emails from this week."
- "Read the full email from Alice about the invoice."
- "Show me the whole thread for that conversation."

**Sending email (gated — you'll approve the draft)**
- "Reply to Alice's email saying I'll have the report by Friday."
- "Send an email to bob@example.com, subject 'Lunch?', asking if he's free Thursday."
- "Forward the invoice email to accounting@example.com with a short note."

**Reading the calendar**
- "What's on my calendar this week?"
- "Read the details of my 2pm meeting tomorrow."
- "Am I free tomorrow 2–3pm?"  *(work/school accounts only)*
- "When are alice@contoso.com and I both free Thursday afternoon?"  *(work/school only)*

**Creating events (gated — you'll approve the details)**
- "Create a 30-minute event tomorrow at 2pm titled 'Project sync'."
- "Schedule a 1-hour meeting Friday 10am called 'Design review', invite alice@contoso.com and bob@contoso.com."
- "Block 9–11am Monday for focus time."

For the gated actions, Claude Desktop shows the exact `send_email(...)` /
`create_event(...)` arguments and waits for your **Approve / Deny**. Want a
change? Tell the agent ("make it 45 minutes", "cc my manager") and it re-proposes.

---

## Audit log

Every gated action appends one JSON line to
`~/.exchange-ai-connector/audit.log`:

- **Sends:** `{ts, to, subject[, reply_to_id]}`
- **Events:** `{ts, kind:"event", subject, start[, attendees]}`

Append-only JSONL, `grep`-able:

```bash
grep '"kind": "event"' ~/.exchange-ai-connector/audit.log
```

---

## Re-consent / token cache

The OAuth token is cached in your OS keychain (service
`exchange-ai-connector`, account `msal-token-cache`) and refreshed silently. The
cached token only carries the scopes you consented to. If you **add a scope**
(e.g. enabling calendar after email-only), clear the cache so the next run
re-prompts the browser with the new scopes:

```bash
python -c "import keyring; keyring.delete_password('exchange-ai-connector','msal-token-cache')"
```

("Not found" just means there was no cache to clear.) Then restart your client.

---

## Scope

- **v1:** email — list/read/thread + gated send.
- **v2 (this release):** calendar — list/read events, free/busy availability,
  and gated `create_event`.

A standalone web approval UI, app-only auth, and multi-account approval remain
deliberately out of scope; see the design specs under `docs/superpowers/specs/`.
