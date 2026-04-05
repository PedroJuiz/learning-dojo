# medium-mcp

An MCP server that gives Claude access to your Medium premium account via Playwright browser automation.

## Tools

| Tool | Description |
|---|---|
| `read_article(url)` | Read the full content of any Medium article (including paywalled ones) |
| `search_medium(query, max_results?)` | Search Medium and return a list of matching articles |

## Setup

### 1. Install dependencies

```bash
cd medium-mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
playwright install chromium
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your Medium email and password
```

> **Note:** Medium must have password login enabled for your account.
> Go to Medium Settings → Security → enable password sign-in.

### 3. Run tests

```bash
pytest
```

### 4. Register with Claude Code

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "medium": {
      "command": "uv",
      "args": ["run", "--directory", "/home/pedroj/projects/learning-dojo/medium-mcp", "medium-mcp"],
      "env": {
        "MEDIUM_EMAIL": "your@email.com",
        "MEDIUM_PASSWORD": "your_password"
      }
    }
  }
}
```

Or use the Claude Code CLI:

```bash
claude mcp add medium -- uv run --directory /home/pedroj/projects/learning-dojo/medium-mcp medium-mcp
```

## How it works

1. On first run, Playwright launches a headless Chromium browser and logs into Medium with your credentials.
2. The session is saved to `.browser_session/state.json` — subsequent runs reuse it without re-logging in.
3. Each tool call opens a new browser tab, extracts the content, and closes it.

## Project structure

```
medium-mcp/
  src/medium_mcp/
    server.py     # MCP server, tool definitions and handlers
    browser.py    # Playwright session management + login
    article.py    # HTML parsing: articles and search results
  tests/
    test_article.py   # Unit tests for parsing logic (no browser)
```
