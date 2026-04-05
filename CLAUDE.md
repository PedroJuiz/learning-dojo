# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Structure

Monorepo of hands-on Claude Code learning projects. Each project lives in its own subfolder with its own `pyproject.toml`, virtual environment, and tests.

| Project | Description |
|---|---|
| `medium-mcp/` | MCP server that reads Medium articles via Playwright |
| `devto-mcp/` | MCP server that searches and reads Dev.to articles via the public REST API |

## Conventions

- Each project is self-contained in its own subfolder with its own dependency manager, tests, and `CLAUDE.md`.
- Run all commands from within the project subfolder, not the repo root.
- Use the idiomatic toolchain for the project's language (e.g. `uv` for Python, `npm`/`pnpm` for TypeScript).

## Adding a new project

1. Create a subfolder with its own source layout, dependency file, and `tests/`.
2. Add a `CLAUDE.md` inside the subfolder covering setup, commands, and architecture.
3. Add a row to the project table above.
