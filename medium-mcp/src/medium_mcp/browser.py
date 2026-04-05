"""Playwright browser session management with persistent authentication."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from playwright.async_api import (
    Browser,
    BrowserContext,
    async_playwright,
    Playwright,
)

_DEFAULT_SESSION_DIR = Path.home() / ".local" / "share" / "medium-mcp"
SESSION_DIR = Path(os.getenv("MEDIUM_SESSION_DIR", _DEFAULT_SESSION_DIR))
MEDIUM_LOGIN_URL = "https://medium.com/m/signin"
MEDIUM_HOME_URL = "https://medium.com"


class BrowserSession:
    """Manages a persistent Playwright browser context for Medium."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        SESSION_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            storage_state=str(SESSION_DIR / "state.json")
            if (SESSION_DIR / "state.json").exists()
            else None,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )

    async def stop(self) -> None:
        if self._context:
            state_path = SESSION_DIR / "state.json"
            await self._context.storage_state(path=str(state_path))
            state_path.chmod(0o600)
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("BrowserSession not started. Call start() first.")
        return self._context

    async def is_authenticated(self) -> bool:
        """Check if the current session is already logged in to Medium."""
        page = await self.context.new_page()
        try:
            await page.goto(MEDIUM_HOME_URL, wait_until="domcontentloaded", timeout=15_000)
            # Medium shows a sign-in button when not authenticated
            sign_in_visible = await page.locator("a[href*='signin']").count()
            return sign_in_visible == 0
        finally:
            await page.close()

    async def ensure_authenticated(self) -> None:
        """Raise if the saved session is missing or expired.

        Medium uses OTP-only login, so automated re-login is not possible.
        Run the one-time setup to create a valid session::

            python -m medium_mcp.setup_auth
        """
        if await self.is_authenticated():
            return

        state_path = SESSION_DIR / "state.json"
        if not state_path.exists():
            raise RuntimeError(
                "No saved Medium session found. "
                "Run `python -m medium_mcp.setup_auth` to log in and save your session."
            )
        raise RuntimeError(
            "Medium session has expired. "
            "Run `python -m medium_mcp.setup_auth` to log in again."
        )


# Module-level singleton used by the MCP server
_session = BrowserSession()


async def get_session() -> BrowserSession:
    return _session


async def session_lifespan() -> AsyncGenerator[BrowserSession, None]:
    """Async context manager for use in the MCP server lifespan."""
    await _session.start()
    await _session.ensure_authenticated()
    try:
        yield _session
    finally:
        await _session.stop()
