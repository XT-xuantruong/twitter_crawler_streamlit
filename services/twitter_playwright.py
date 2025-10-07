import time, random, json
from typing import Optional, List, Dict, Generator, Tuple
import pandas as pd
from playwright.sync_api import Page
from services.browser import launch_browser
from utils.schema import normalize_records
from utils.twitter_helpers import (
    post_id_from_href,
    parse_metrics_from_aria,
    normalize_cookies
)
from utils.checkpoint import Checkpoint
from core.config import Config


class PlaywrightTwitterScraper:
    def __init__(
        self,
        headless: bool = True,
        cookies_path: Optional[str] = None,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        checkpoint_path: Optional[str] = None
    ):
        """Initialize Playwright browser and page."""
        self.pw, self.browser, self.context, self.page = launch_browser(
            headless=headless,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/130.0.0.0 Safari/537.36"
        )
        self.cp = Checkpoint(checkpoint_path) if checkpoint_path else None
        if cookies_path:
            self._load_cookies(cookies_path)

    def _load_cookies(self, cookies_path: str):
        try:
            with open(cookies_path, "r", encoding="utf-8") as f:
                cookies = normalize_cookies(json.load(f))
                self.context.add_cookies(cookies)
            self.page.goto("https://x.com/home", timeout=60000)
            print(f"[INFO] Cookies loaded, current URL: {self.page.url}")
        except Exception as e:
            print(f"[WARN] Failed to load cookies: {e}")

    def close(self):
        """Close all browser resources safely."""
        for obj in [self.page, self.context, self.browser]:
            try:
                obj.close()
            except Exception:
                pass
        try:
            self.pw.stop()
        except Exception:
            pass

    # ---------------------- MAIN CRAWLING ----------------------

    def _parse_cards(self) -> List[Dict]:
        """Extract tweets currently visible on the page."""
        cards = self.page.query_selector_all("article[role='article']")
        rows = []
        for a in cards:
            try:
                href_el = a.query_selector("a[href*='/status/']")
                href = href_el.get_attribute("href") if href_el else None
                tid = post_id_from_href(href)
                if not tid:
                    continue
                t_el = a.query_selector("time")
                created_at = t_el.get_attribute("datetime") if t_el else None
                content = a.inner_text()
                metrics_el = a.query_selector("div[role='group'][aria-label]")
                metrics = parse_metrics_from_aria(
                    metrics_el.get_attribute("aria-label") if metrics_el else None
                )
                username = None
                u = a.query_selector("a[href^='/' i]")
                if u:
                    prof_href = u.get_attribute("href")
                    if prof_href and len(prof_href.strip("/").split("/")) == 1:
                        username = prof_href.strip("/")
                rows.append({
                    "post_id": tid,
                    "text": content,
                    "link": f"https://x.com{href}" if href else None,
                    "created_at": created_at,
                    "username": username,
                    "like_count": metrics.get("like_count"),
                    "retweet_count": metrics.get("repost_count"),
                    "reply_count": metrics.get("reply_count"),
                    "view_count": metrics.get("view_count"),
                })
            except Exception:
                continue
        return rows

    def search(
        self,
        raw_query: str,
        limit: int = Config.DEFAULT_LIMIT,
        lang: Optional[str] = Config.DEFAULT_LANG,
        batch_size: int = Config.BATCH_SIZE,
        save_batch_fn=None,
    ) -> Generator[Tuple[pd.DataFrame, Dict], None, None]:
        """Search tweets by keyword and yield batches."""
        query = f"{raw_query} lang:{lang}" if lang and f"lang:{lang}" not in raw_query else raw_query
        self.page.goto(f"https://x.com/search?q={query}&f=live", wait_until="domcontentloaded", timeout=60000)
        time.sleep(random.uniform(*Config.FIRST_LOAD_DELAY))

        seen = set(self.cp.data.get("seen_ids", [])) if self.cp else set()
        buffer, collected, stagnation, last_seen = [], 0, 0, len(seen)

        while collected < limit:
            rows = self._parse_cards()
            new_rows = [r for r in rows if r["post_id"] not in seen]
            for r in new_rows:
                seen.add(r["post_id"])
                buffer.append(r)
                collected += 1
                if collected >= limit:
                    break

            if len(buffer) >= batch_size:
                df = normalize_records(buffer[:batch_size])
                if save_batch_fn:
                    save_batch_fn(df, {"collected": collected})
                if self.cp:
                    self.cp.add_seen([x["post_id"] for x in buffer[:batch_size]])
                yield df, {"collected": collected}
                buffer = buffer[batch_size:]

            self.page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*Config.SCROLL_DELAY))

            stagnation = stagnation + 1 if len(seen) == last_seen else 0
            last_seen = len(seen)
            if stagnation >= Config.STAGNATION_LIMIT:
                break

        if buffer:
            df = normalize_records(buffer)
            if save_batch_fn:
                save_batch_fn(df, {"collected": collected})
            yield df, {"collected": collected}
