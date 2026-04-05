# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
```

No browser or auth setup required — Dev.to's public API needs no credentials.

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

Two layers:

- **`server.py`** — MCP entry point. Registers `search_articles` and `read_article` tools and wires them to the article module. No lifespan or session management needed.
- **`article.py`** — Pure async functions using `httpx`. `_parse_article` and `_parse_search_results` are private pure functions (no I/O) tested directly in `tests/test_article.py` without live HTTP.

### Key design difference from medium-mcp

Medium required Playwright (browser automation + cookie auth) because of the paywall. Dev.to has a public REST API, so this server uses plain `httpx` HTTP calls — no browser, no auth, no session state.

### Search endpoint

Dev.to's free-text search uses the undocumented endpoint:

```
GET https://dev.to/search/feed_content?per_page=N&search_fields=<query>
```

The documented `/api/articles` endpoint only supports tag/username filtering, not free-text.

### Article endpoint

```
GET https://dev.to/api/articles/{username}/{slug}
```

Returns full article data including `body_markdown` (preferred) or `body_html`.

## MCP registration

```json
{
  "mcpServers": {
    "devto": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/devto-mcp", "devto-mcp"]
    }
  }
}
```
