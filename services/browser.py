from playwright.sync_api import sync_playwright
from typing import Optional, Tuple

def launch_browser(
    headless: bool = True,
    user_agent: Optional[str] = None
) -> Tuple:
    """
    Launch Chromium browser (no proxy) with sensible defaults.
    """
    pw = sync_playwright().start()

    launch_args = {
        "headless": headless,
        "args": [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1280,800",
            "--disable-gpu",
            "--disable-dev-shm-usage"
        ]
    }

    browser = pw.chromium.launch(**launch_args)

    context_args = {
        "viewport": {"width": 1280, "height": 800},
        "ignore_https_errors": True,
    }

    if user_agent:
        context_args["user_agent"] = user_agent
    else:
        # Default UA updated to Chrome 130 to look more realistic
        context_args["user_agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        )

    context = browser.new_context(**context_args)
    page = context.new_page()

    # Set global timeout longer for slow connections
    page.set_default_timeout(180000)

    print(f"✅ Browser launched successfully (headless={headless}, direct connection)")
    print(f"🕵️ User-Agent: {context_args['user_agent']}")

    return pw, browser, context, page
