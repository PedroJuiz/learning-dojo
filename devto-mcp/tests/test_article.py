"""Unit tests for Dev.to API parsing — no live HTTP calls."""

from __future__ import annotations

import pytest

from devto_mcp.article import _parse_article, _parse_search_results, _parse_url


# ---------------------------------------------------------------------------
# _parse_url
# ---------------------------------------------------------------------------

def test_parse_url_full_https() -> None:
    username, slug = _parse_url("https://dev.to/ben/explain-the-concept-of-closure")
    assert username == "ben"
    assert slug == "explain-the-concept-of-closure"


def test_parse_url_trailing_slash() -> None:
    username, slug = _parse_url("https://dev.to/ben/some-article/")
    assert username == "ben"
    assert slug == "some-article"


def test_parse_url_http() -> None:
    username, slug = _parse_url("http://dev.to/alice/my-post")
    assert username == "alice"
    assert slug == "my-post"


def test_parse_url_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Cannot parse"):
        _parse_url("https://dev.to/justonepart")


# ---------------------------------------------------------------------------
# _parse_article
# ---------------------------------------------------------------------------

ARTICLE_FIXTURE: dict[str, object] = {
    "title": "Getting started with MCP servers",
    "body_markdown": "## Introduction\n\nModel Context Protocol is great.",
    "reading_time_minutes": 5,
    "tag_list": ["mcp", "claudeai", "python"],
    "user": {"name": "Pedro Junqueira", "username": "pedroj"},
}


def test_parse_article_title() -> None:
    article = _parse_article("https://dev.to/pedroj/getting-started", ARTICLE_FIXTURE)
    assert article.title == "Getting started with MCP servers"


def test_parse_article_author() -> None:
    article = _parse_article("https://dev.to/pedroj/getting-started", ARTICLE_FIXTURE)
    assert article.author == "Pedro Junqueira"


def test_parse_article_reading_time() -> None:
    article = _parse_article("https://dev.to/pedroj/getting-started", ARTICLE_FIXTURE)
    assert article.reading_time == "5 min read"


def test_parse_article_tags() -> None:
    article = _parse_article("https://dev.to/pedroj/getting-started", ARTICLE_FIXTURE)
    assert article.tags == ["mcp", "claudeai", "python"]


def test_parse_article_content() -> None:
    article = _parse_article("https://dev.to/pedroj/getting-started", ARTICLE_FIXTURE)
    assert "Model Context Protocol" in article.content


def test_parse_article_fallback_username() -> None:
    data = {**ARTICLE_FIXTURE, "user": {"username": "pedroj"}}
    article = _parse_article("https://dev.to/pedroj/getting-started", data)
    assert article.author == "pedroj"


def test_parse_article_missing_user() -> None:
    data = {**ARTICLE_FIXTURE, "user": {}}
    article = _parse_article("https://dev.to/pedroj/getting-started", data)
    assert article.author == "Unknown author"


def test_parse_article_prefers_markdown_over_html() -> None:
    data = {**ARTICLE_FIXTURE, "body_html": "<p>HTML version</p>"}
    article = _parse_article("https://dev.to/pedroj/getting-started", data)
    assert "Model Context Protocol" in article.content  # markdown wins


# ---------------------------------------------------------------------------
# _parse_search_results
# ---------------------------------------------------------------------------

SEARCH_FIXTURE: list[object] = [
    {
        "title": "Claude Code tips",
        "url": "https://dev.to/alice/claude-code-tips",
        "description": "A guide to Claude Code workflows.",
        "tag_list": ["claudeai", "productivity"],
        "user": {"name": "Alice", "username": "alice"},
    },
    {
        "title": "Building MCP servers",
        "url": "https://dev.to/bob/building-mcp-servers",
        "description": "Step by step MCP tutorial.",
        "tag_list": ["mcp", "python"],
        "user": {"name": "Bob", "username": "bob"},
    },
]


def test_parse_search_results_count() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=10)
    assert len(results) == 2


def test_parse_search_results_title() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=10)
    assert results[0].title == "Claude Code tips"


def test_parse_search_results_url() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=10)
    assert results[0].url == "https://dev.to/alice/claude-code-tips"  # url field used directly


def test_parse_search_results_author() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=10)
    assert results[0].author == "Alice"


def test_parse_search_results_tags() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=10)
    assert results[1].tags == ["mcp", "python"]


def test_parse_search_results_max_results() -> None:
    results = _parse_search_results(SEARCH_FIXTURE, max_results=1)
    assert len(results) == 1


def test_parse_search_results_empty() -> None:
    results = _parse_search_results([], max_results=10)
    assert results == []


def test_parse_search_results_not_a_list() -> None:
    results = _parse_search_results({}, max_results=10)  # type: ignore[arg-type]
    assert results == []
