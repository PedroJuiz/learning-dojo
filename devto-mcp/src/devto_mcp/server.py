"""MCP server entry point — exposes Dev.to reading tools to Claude."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from devto_mcp.article import read_article, search_articles

app = Server("devto-mcp")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_articles",
            description=(
                "Search Dev.to for articles matching a free-text query. "
                "Returns a list of results with titles, URLs, authors, tags, and previews."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text search query (e.g. 'How to use worktrees in Claude Code').",
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
        Tool(
            name="read_article",
            description=(
                "Read the full content of a Dev.to article. "
                "Returns the title, author, reading time, tags, and full body in Markdown format."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the Dev.to article (e.g. https://dev.to/username/article-slug).",
                    }
                },
                "required": ["url"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "search_articles":
        query = arguments["query"]
        if len(query) > 500:
            raise ValueError("Query too long (max 500 characters)")
        max_results = max(1, min(int(arguments.get("max_results", 10)), 20))
        results = await search_articles(query, max_results)
        if not results:
            return [TextContent(type="text", text="No results found.")]
        lines = [f"## Dev.to search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.title}**")
            if r.author:
                lines.append(f"   _by {r.author}_")
            if r.tags:
                lines.append(f"   Tags: {', '.join(r.tags)}")
            if r.preview:
                lines.append(f"   {r.preview}")
            lines.append(f"   {r.url}\n")
        return [TextContent(type="text", text="\n".join(lines))]

    if name == "read_article":
        url = arguments["url"]
        article = await read_article(url)
        text = (
            f"# {article.title}\n\n"
            f"**Author:** {article.author}  \n"
            f"**Reading time:** {article.reading_time}  \n"
            f"**Tags:** {', '.join(article.tags)}\n\n"
            f"---\n\n"
            f"{article.content}"
        )
        return [TextContent(type="text", text=text)]

    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
