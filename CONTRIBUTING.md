# Contributing

Thanks for your interest in `exchange-ai-connector`.

## Development setup

```bash
git clone https://github.com/wteja/exchange-ai-connector.git
cd exchange-ai-connector
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

Tests mock all Microsoft Graph calls — no live mailbox or network is required.
Keep the suite green and the output pristine (no stray warnings) before opening
a PR.

## Conventions

- **TDD:** write a failing test, make it pass, keep the diff minimal.
- **Layering:** `graph.py` / `calendar.py` know nothing about MCP; `server.py`
  knows nothing about HTTP. New Graph endpoints go in the connector layer; new
  tools wire them up in `server.py`.
- **State-changing tools are gated.** Any tool that mutates the mailbox or
  calendar must carry the destructive annotation so the MCP client confirms
  before running, and should append an audit line.
- Match the style of the surrounding code.

## Pull requests

Keep PRs focused on one change. Describe what it does, how you tested it, and
any account-type caveats (e.g. work/school vs personal Microsoft accounts).

## Releasing

Publishing to PyPI is automated via `.github/workflows/publish.yml` using PyPI
Trusted Publishing (no API token stored).

One-time setup: on PyPI, register a trusted publisher for this project
(repo `wteja/exchange-ai-connector`, workflow `publish.yml`, environment `pypi`).
See https://docs.pypi.org/trusted-publishers/.

To cut a release: bump `version` in `pyproject.toml`, then publish a GitHub
Release with a matching tag (e.g. `v0.2.0`). The workflow builds the sdist +
wheel and uploads them. Build locally to check first: `python -m build`.
