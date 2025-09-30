from playwright.sync_api import sync_playwright, Browser
from typing import Optional

def launch_browser(headless: bool = True, proxy: Optional[str] = None) -> (any, Browser):
    pw = sync_playwright().start()
    launch_args = {
        "headless": headless,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"]
    }
    if proxy:
        launch_args["proxy"] = {"server": proxy}
    browser = pw.chromium.launch(**launch_args)
    return pw, browser
