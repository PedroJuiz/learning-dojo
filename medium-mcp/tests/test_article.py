"""Unit tests for article parsing logic (no browser required)."""

from medium_mcp.article import _parse_article, _parse_search_results


SAMPLE_ARTICLE_HTML = """
<html><body>
<article>
  <h1>How Claude Code Changed My Workflow</h1>
  <a data-testid="authorName" href="/u/pedro">Pedro Juiz</a>
  <span>5 min read</span>
  <p>Claude Code is an AI-powered CLI tool.</p>
  <h2>Getting Started</h2>
  <p>Install it with <code>npm install -g @anthropic-ai/claude-code</code>.</p>
  <blockquote>The best tool I have used in years.</blockquote>
  <pre>claude --help</pre>
</article>
</body></html>
"""

SAMPLE_SEARCH_HTML = """
<html><body>
  <article>
    <h2>Claude Code Tips</h2>
    <a href="/p/claude-code-tips" data-testid="link">Read</a>
    <a data-testid="authorName">Jane Doe</a>
    <p>Top 10 tips for using Claude Code effectively.</p>
  </article>
  <article>
    <h2>MCP Servers Explained</h2>
    <a href="https://medium.com/p/mcp-explained">Read</a>
    <a data-testid="authorName">John Smith</a>
    <p>A deep dive into Model Context Protocol.</p>
  </article>
</body></html>
"""


def test_parse_article_title() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert article.title == "How Claude Code Changed My Workflow"


def test_parse_article_author() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert article.author == "Pedro Juiz"


def test_parse_article_reading_time() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert "5 min read" in article.reading_time


def test_parse_article_content_includes_paragraphs() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert "Claude Code is an AI-powered CLI tool." in article.content


def test_parse_article_content_formats_headings() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert "## Getting Started" in article.content


def test_parse_article_content_formats_blockquote() -> None:
    article = _parse_article("https://medium.com/p/test", SAMPLE_ARTICLE_HTML)
    assert "> The best tool I have used in years." in article.content


def test_parse_search_results_count() -> None:
    results = _parse_search_results(SAMPLE_SEARCH_HTML, max_results=10)
    assert len(results) == 2


def test_parse_search_results_titles() -> None:
    results = _parse_search_results(SAMPLE_SEARCH_HTML, max_results=10)
    assert results[0].title == "Claude Code Tips"
    assert results[1].title == "MCP Servers Explained"


def test_parse_search_results_max_results() -> None:
    results = _parse_search_results(SAMPLE_SEARCH_HTML, max_results=1)
    assert len(results) == 1


def test_parse_search_results_absolute_url() -> None:
    results = _parse_search_results(SAMPLE_SEARCH_HTML, max_results=10)
    assert results[0].url.startswith("https://medium.com")
