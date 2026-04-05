"""Article and search content extraction from Medium pages."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup, Tag

from medium_mcp.browser import BrowserSession

logger = logging.getLogger(__name__)


@dataclass
class Article:
    url: str
    title: str
    author: str
    reading_time: str
    content: str


@dataclass
class SearchResult:
    title: str
    url: str
    author: str
    preview: str


def _validate_medium_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"URL must use https, got: {parsed.scheme!r}")
    host = parsed.netloc.lower()
    if host != "medium.com" and not host.endswith(".medium.com"):
        raise ValueError(f"URL must be on medium.com, got: {parsed.netloc!r}")


async def read_article(session: BrowserSession, url: str) -> Article:
    """Navigate to a Medium article URL and extract its full content."""
    _validate_medium_url(url)
    page = await session.context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        # Dismiss cookie/membership popups if present
        for selector in ["[data-testid='close-button']", "button[aria-label='close']"]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2_000):
                    await btn.click()
            except Exception as exc:
                logger.debug("Popup dismiss skipped for %r: %s", selector, exc)

        # Wait for the article body — try multiple selectors
        for selector in ("article", "main", "[data-testid='storyContent']", "h1"):
            try:
                await page.wait_for_selector(selector, timeout=10_000)
                break
            except Exception as exc:
                logger.debug("Selector %r not found: %s", selector, exc)
                continue

        html = await page.content()
    finally:
        await page.close()

    return _parse_article(url, html)


def _parse_article(url: str, html: str) -> Article:
    soup = BeautifulSoup(html, "lxml")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown title"

    # Author — Medium puts it in a link near the top byline
    author = "Unknown author"
    author_tag = soup.select_one("a[data-testid='authorName']")
    if not author_tag:
        # Fallback: look for rel=author link
        author_tag = soup.find("a", rel="author")
    if author_tag:
        author = author_tag.get_text(strip=True)

    # Reading time
    reading_time = ""
    rt_tag = soup.find("span", string=lambda t: t and "min read" in t)
    if rt_tag:
        reading_time = rt_tag.get_text(strip=True)

    # Body — extract all paragraph and heading text inside <article> or <main>
    article_tag = soup.find("article") or soup.find("main")
    content = ""
    if isinstance(article_tag, Tag):
        blocks = article_tag.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"])
        lines: list[str] = []
        for block in blocks:
            text = block.get_text(separator=" ", strip=True)
            if text:
                if block.name in ("h1", "h2", "h3", "h4"):
                    lines.append(f"\n## {text}\n")
                elif block.name == "blockquote":
                    lines.append(f"> {text}")
                elif block.name == "pre":
                    lines.append(f"```\n{text}\n```")
                else:
                    lines.append(text)
        content = "\n".join(lines)

    return Article(url=url, title=title, author=author, reading_time=reading_time, content=content)


async def search_medium(session: BrowserSession, query: str, max_results: int = 10) -> list[SearchResult]:
    """Search Medium and return a list of article results."""
    search_url = f"https://medium.com/search?{urlencode({'q': query})}"
    page = await session.context.new_page()
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_selector("article", timeout=10_000)
        html = await page.content()
    finally:
        await page.close()

    return _parse_search_results(html, max_results)


def _parse_search_results(html: str, max_results: int) -> list[SearchResult]:
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []

    for article in soup.find_all("article")[:max_results]:
        if not isinstance(article, Tag):
            continue

        # Title is usually the first h2 or h3
        title_tag = article.find(["h2", "h3"])
        title = title_tag.get_text(strip=True) if title_tag else ""

        # URL — walk up from the title tag to find its enclosing <a>
        url = ""
        if title_tag:
            node = title_tag.parent
            while node and node.name != "article":
                if node.name == "a":
                    href = node.get("href", "")
                    if isinstance(href, str) and href:
                        url = href if href.startswith("http") else f"https://medium.com{href}"
                    break
                node = node.parent
        # Fallback: first link whose path looks like an article (has a slug segment)
        if not url:
            for a in article.find_all("a", href=True):
                href = a.get("href", "")
                if not isinstance(href, str):
                    continue
                # Article URLs have at least 3 path segments or contain /@.../slug
                path = href.split("?")[0]
                segments = [s for s in path.split("/") if s]
                if len(segments) >= 3 or (len(segments) == 2 and "-" in segments[-1]):
                    url = href if href.startswith("http") else f"https://medium.com{href}"
                    break

        # Author
        author_tag = article.select_one("a[data-testid='authorName']") or article.find("a", rel="author")
        author = author_tag.get_text(strip=True) if author_tag else ""

        # Preview — first <p> in the article card
        preview_tag = article.find("p")
        preview = preview_tag.get_text(strip=True) if preview_tag else ""

        if title and url:
            results.append(SearchResult(title=title, url=url, author=author, preview=preview))

    return results
