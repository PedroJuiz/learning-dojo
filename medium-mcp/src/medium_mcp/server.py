"""MCP server entry point — exposes Medium reading tools to Claude."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from medium_mcp.article import read_article, search_medium
from medium_mcp.browser import BrowserSession, session_lifespan

load_dotenv()

app = Server("medium-mcp")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="read_article",
            description=(
                "Read the full content of a Medium article (including premium/paywalled ones). "
                "Returns the title, author, reading time, and full body text in Markdown format."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the Medium article to read.",
                    }
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="search_medium",
            description=(
                "Search Medium for articles matching a query. "
                "Returns a list of results with titles, URLs, authors, and preview text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. 'Claude Code MCP servers').",
                        "maxLength": 500,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, max: 20).",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    session: BrowserSession = app.state["session"]  # type: ignore[index]

    if name == "read_article":
        url = arguments["url"]
        article = await read_article(session, url)
        text = (
            f"# {article.title}\n\n"
            f"**Author:** {article.author}  \n"
            f"**Reading time:** {article.reading_time}\n\n"
            f"---\n\n"
            f"{article.content}"
        )
        return [TextContent(type="text", text=text)]

    if name == "search_medium":
        query = arguments["query"]
        if len(query) > 500:
            raise ValueError("Query too long (max 500 characters)")
        max_results = max(1, min(int(arguments.get("max_results", 10)), 20))
        results = await search_medium(session, query, max_results)
        if not results:
            return [TextContent(type="text", text="No results found.")]
        lines = [f"## Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.title}**")
            if r.author:
                lines.append(f"   _by {r.author}_")
            if r.preview:
                lines.append(f"   {r.preview}")
            lines.append(f"   {r.url}\n")
        return [TextContent(type="text", text="\n".join(lines))]

    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Lifespan & entrypoint
# ---------------------------------------------------------------------------

@asynccontextmanager
async def managed_lifespan() -> AsyncGenerator[None, None]:
    async for session in session_lifespan():
        app.state = {"session": session}  # type: ignore[attr-defined]
        yield


def main() -> None:
    async def _run() -> None:
        async with managed_lifespan():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
