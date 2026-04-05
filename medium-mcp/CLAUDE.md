# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
playwright install chromium
```

First-time auth (opens a real browser for OTP login — run once):
```bash
python -m medium_mcp.setup_auth
```

## Commands

```bash
# Run all tests
pytest

# Run a single test
pytest tests/test_article.py::test_parse_article_title

# Lint and format
ruff check src tests
ruff format src tests

# Type check
mypy src
```

## Architecture

Three layers:

- **`server.py`** — MCP entry point. Registers `read_article` and `search_medium` tools, holds the `BrowserSession` singleton in `app.state`, and wires the lifespan context manager.
- **`browser.py`** — Manages a single persistent Playwright `BrowserContext`. Session cookies are saved to `~/.local/share/medium-mcp/state.json` (outside the repo, `0o600` permissions) after each run and reloaded on the next. Override the path with `MEDIUM_SESSION_DIR`. `ensure_authenticated()` raises (rather than re-logging in) if the session is expired, because Medium uses OTP-only login.
- **`article.py`** — Pure HTML parsing (BeautifulSoup + lxml). `_parse_article` and `_parse_search_results` are the private functions tested directly in `tests/test_article.py` without needing a live browser.

**`setup_auth.py`** is a standalone interactive script (not part of the server) that opens a headed browser for the one-time OTP login and saves the resulting cookies.

## MCP registration

```json
{
  "mcpServers": {
    "medium": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/medium-mcp", "medium-mcp"]
    }
  }
}
```

The session is stored in `~/.local/share/medium-mcp/state.json` by default (outside the repo, permissions `0o600`). Override with the `MEDIUM_SESSION_DIR` environment variable if needed.
