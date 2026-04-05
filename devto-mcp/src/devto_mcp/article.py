"""Dev.to API client — free-text search and article fetching."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import httpx

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_\-]+$")

BASE_URL = "https://dev.to"
API_BASE = f"{BASE_URL}/api"
SEARCH_URL = f"{API_BASE}/articles/search"

HEADERS = {
    "User-Agent": "devto-mcp/0.1.0",
    "Accept": "application/json",
}


@dataclass
class Article:
    url: str
    title: str
    author: str
    reading_time: str
    tags: list[str] = field(default_factory=list)
    content: str = ""


@dataclass
class SearchResult:
    title: str
    url: str
    author: str
    preview: str
    tags: list[str] = field(default_factory=list)


async def search_articles(query: str, max_results: int = 10) -> list[SearchResult]:
    """Search Dev.to using free-text via the undocumented feed_content endpoint."""
    params = {"per_page": max_results, "q": query}
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        response = await client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        items: list[object] = response.json()
    return _parse_search_results(items, max_results)


def _parse_search_results(items: list[object], max_results: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    if not isinstance(items, list):
        return results
    for item in items[:max_results]:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", ""))
        user = item.get("user", {})
        author = ""
        if isinstance(user, dict):
            author = str(user.get("name", "") or user.get("username", ""))
        tag_list = item.get("tag_list", [])
        tags = tag_list if isinstance(tag_list, list) else []
        results.append(
            SearchResult(
                title=str(item.get("title", "")),
                url=url,
                author=author,
                preview=str(item.get("description", "")),
                tags=[str(t) for t in tags],
            )
        )
    return results


async def read_article(url: str) -> Article:
    """Fetch a Dev.to article by URL, returning full Markdown content."""
    username, slug = _parse_url(url)
    api_url = f"{API_BASE}/articles/{username}/{slug}"
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        response = await client.get(api_url)
        response.raise_for_status()
        data: dict[str, object] = response.json()
    return _parse_article(url, data)


def _parse_url(url: str) -> tuple[str, str]:
    """Extract (username, slug) from a Dev.to article URL."""
    path = url.rstrip("/")
    for prefix in ("https://dev.to", "http://dev.to"):
        if path.startswith(prefix):
            path = path[len(prefix):]
            break
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Cannot parse username/slug from URL: {url}")
    username, slug = parts[0], parts[1]
    if not _SAFE_SEGMENT.match(username) or not _SAFE_SEGMENT.match(slug):
        raise ValueError(f"Invalid characters in URL: {url}")
    return username, slug


def _parse_article(url: str, data: dict[str, object]) -> Article:
    user = data.get("user", {})
    author = "Unknown author"
    if isinstance(user, dict):
        author = str(user.get("name", "") or user.get("username", "Unknown author"))
    reading_time_minutes = data.get("reading_time_minutes", "?")
    reading_time = f"{reading_time_minutes} min read"
    tag_list = data.get("tag_list", [])
    tags = [str(t) for t in tag_list] if isinstance(tag_list, list) else []
    content = str(data.get("body_markdown") or data.get("body_html") or "")
    return Article(
        url=url,
        title=str(data.get("title", "Unknown title")),
        author=author,
        reading_time=reading_time,
        tags=tags,
        content=content,
    )
