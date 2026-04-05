"""One-time interactive login to save a Medium browser session.

Run this once before starting the MCP server:

    python -m medium_mcp.setup_auth

A visible browser window will open. Log in to Medium (enter your email and
the OTP code Medium sends you). Once you land on the Medium home page, this
script saves the session cookies and exits. The MCP server will reuse those
cookies on every subsequent run.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

load_dotenv()

_DEFAULT_SESSION_DIR = Path.home() / ".local" / "share" / "medium-mcp"
SESSION_DIR = Path(os.getenv("MEDIUM_SESSION_DIR", _DEFAULT_SESSION_DIR))
MEDIUM_HOME_URL = "https://medium.com"
MEDIUM_LOGIN_URL = "https://medium.com/m/signin"

POLL_INTERVAL_S = 2
LOGIN_TIMEOUT_S = 300  # 5 minutes


async def setup() -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path = SESSION_DIR / "state.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        # Hide the navigator.webdriver flag that sites use to detect automation
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()
        await page.goto(MEDIUM_LOGIN_URL, wait_until="domcontentloaded")

        print("Browser opened. Log in to Medium:")
        print("  1. Enter your email address")
        print("  2. Check your inbox for the OTP code and enter it")
        print("  3. Wait — this script will detect when you're logged in and save the session")
        print(f"\nTimeout: {LOGIN_TIMEOUT_S}s")

        elapsed = 0
        authenticated = False
        while elapsed < LOGIN_TIMEOUT_S:
            await asyncio.sleep(POLL_INTERVAL_S)
            elapsed += POLL_INTERVAL_S
            try:
                current_url = page.url
                # Medium redirects to home or a feed URL after successful login
                if "medium.com" in current_url and "/m/signin" not in current_url:
                    sign_in_links = await page.locator("a[href*='signin']").count()
                    if sign_in_links == 0:
                        authenticated = True
                        break
            except Exception as exc:
                logger.debug("Login poll error (page may be navigating): %s", exc)

        if not authenticated:
            print("\nTimed out waiting for login. Re-run this script and try again.")
            await browser.close()
            sys.exit(1)

        await context.storage_state(path=str(state_path))
        state_path.chmod(0o600)
        await browser.close()

    print(f"\nSession saved to {state_path}")
    print("You can now start the MCP server — it will use this session automatically.")
    print(f"To use a custom location, set the MEDIUM_SESSION_DIR environment variable.")


def main() -> None:
    asyncio.run(setup())


if __name__ == "__main__":
    main()
