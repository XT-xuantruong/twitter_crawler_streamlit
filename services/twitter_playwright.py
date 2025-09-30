import os
import json
import time
import random
import pandas as pd
from typing import List, Dict, Any, Optional, Generator, Tuple
from playwright.sync_api import Page

from services.browser import launch_browser
from utils.schema import normalize_records
from utils.checkpoint import Checkpoint
from utils.twitter_helpers import parse_metrics_from_aria, normalize_cookies, post_id_from_href
from core.config import Config


class PlaywrightTwitterScraper:
    def __init__(
        self,
        headless: bool = True,
        checkpoint_path: Optional[str] = None,
        proxy: Optional[str] = None,
        cookies_path: Optional[str] = None,
    ):
        self.pw, self.browser = launch_browser(headless=headless, proxy=proxy)
        ua = random.choice(Config.USER_AGENTS)
        self.page: Page = self.browser.new_page(user_agent=ua)
        self.cp = Checkpoint(checkpoint_path) if checkpoint_path else None

        if cookies_path and os.path.exists(cookies_path):
            try:
                with open(cookies_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                # Chuẩn hoá sameSite
                cookies = normalize_cookies(cookies)

                # Debug: in ra tên các cookie
                names = [c.get("name") for c in cookies]
                print(f"[INFO] Loaded {len(cookies)} cookies: {names[:10]} ...")

                # Kiểm tra auth_token và ct0
                if not any(c.get("name") == "auth_token" for c in cookies):
                    print("[WARN] ❌ Cookie file thiếu auth_token → sẽ bị yêu cầu login")
                if not any(c.get("name") == "ct0" for c in cookies):
                    print("[WARN] ❌ Cookie file thiếu ct0 → nhiều request sẽ fail CSRF")

                # Add cookies vào context trước khi mở page
                self.page.context.add_cookies(cookies)

                # Test login bằng cách mở trang home
                self.page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                print(f"[DEBUG] After cookie load, current URL: {self.page.url}")
            except Exception as e:
                print(f"[WARN] Không load cookies: {e}")


    def close(self):
        for obj in [self.page, self.browser, self.pw]:
            try:
                if hasattr(obj, "close"):
                    obj.close()
                elif hasattr(obj, "stop"):
                    obj.stop()
            except Exception:
                pass

    def _parse_cards(self, lang: Optional[str]) -> List[Dict[str, Any]]:
        cards = self.page.query_selector_all("article[role='article']") or \
                self.page.query_selector_all("div[data-testid='tweet']")
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

                username = None
                u = a.query_selector("a[href^='/' i]")
                if u:
                    prof_href = u.get_attribute("href")
                    if prof_href and len(prof_href.strip("/").split("/")) == 1:
                        username = prof_href.strip("/")

                metrics_el = a.query_selector("div[role='group'][aria-label]")
                aria = metrics_el.get_attribute("aria-label") if metrics_el else None
                metrics = parse_metrics_from_aria(aria)

                rows.append({
                    "platform": "twitter",
                    "post_id": tid,
                    "text": content,
                    "language": lang,
                    "created_at": created_at,
                    "user_id": None,
                    "username": username,
                    "displayname": None,
                    "verified_flag": None,
                    "followers_count": None,
                    "friends_count": None,
                    "statuses_count": None,
                    "like_count": metrics.get("like_count"),
                    "retweet_count": metrics.get("repost_count"),
                    "reply_count": metrics.get("reply_count"),
                    "quote_count": None,
                    "hashtags": [],
                    "urls": [href] if href else [],
                    "link": f"https://x.com{href}" if href else None,
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
    ) -> Generator[Tuple[pd.DataFrame, Dict[str, Any]], None, None]:
        q = raw_query
        if lang and f"lang:{lang}" not in q:
            q += f" lang:{lang}"
        url = f"https://x.com/search?q={q}&f=live"

        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(random.uniform(*Config.FIRST_LOAD_DELAY))

        seen = set(self.cp.data.get("seen_ids", [])) if self.cp else set()
        buffer, collected_total, stagnation, last_seen_count = [], 0, 0, len(seen)

        while collected_total < limit:
            rows = self._parse_cards(lang)
            if not rows:
                break

            new_rows = [r for r in rows if r["post_id"] not in seen]
            for r in new_rows:
                seen.add(r["post_id"])
                buffer.append(r)
                collected_total += 1
                if collected_total >= limit:
                    break

            if len(buffer) >= batch_size:
                df = normalize_records(buffer[:batch_size])
                if save_batch_fn:
                    save_batch_fn(df, {"collected": collected_total})
                if self.cp:
                    self.cp.add_seen([x["post_id"] for x in buffer[:batch_size]])
                yield df, {"collected": collected_total}
                buffer = buffer[batch_size:]

            self.page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*Config.SCROLL_DELAY))

            if len(seen) == last_seen_count:
                stagnation += 1
            else:
                stagnation, last_seen_count = 0, len(seen)
            if stagnation >= Config.STAGNATION_LIMIT:
                break

        if buffer:
            df = normalize_records(buffer)
            if save_batch_fn:
                save_batch_fn(df, {"collected": collected_total})
            if self.cp:
                self.cp.add_seen([x["post_id"] for x in buffer])
            yield df, {"collected": collected_total}

    def user_tweets(
        self,
        username: str,
        limit: int = Config.DEFAULT_LIMIT,
        batch_size: int = Config.BATCH_SIZE,
        save_batch_fn=None,
    ) -> Generator[Tuple[pd.DataFrame, Dict[str, Any]], None, None]:
        url = f"https://x.com/{username}"
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(random.uniform(*Config.FIRST_LOAD_DELAY))

        seen = set(self.cp.data.get("seen_ids", [])) if self.cp else set()
        buffer, collected_total, stagnation, last_seen_count = [], 0, 0, len(seen)

        while collected_total < limit:
            rows = self._parse_cards(lang=None)
            for r in rows:
                r["username"] = username
                if not r.get("link") and r.get("post_id"):
                    r["link"] = f"https://x.com/{username}/status/{r['post_id']}"

            new_rows = [r for r in rows if r["post_id"] not in seen]
            if not new_rows:
                stagnation += 1
                if stagnation >= Config.STAGNATION_LIMIT:
                    break
            for r in new_rows:
                seen.add(r["post_id"])
                buffer.append(r)
                collected_total += 1
                if collected_total >= limit:
                    break

            if len(buffer) >= batch_size:
                df = normalize_records(buffer[:batch_size])
                if save_batch_fn:
                    save_batch_fn(df, {"collected": collected_total})
                if self.cp:
                    self.cp.add_seen([x["post_id"] for x in buffer[:batch_size]])
                yield df, {"collected": collected_total}
                buffer = buffer[batch_size:]

            self.page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*Config.SCROLL_DELAY))

        if buffer:
            df = normalize_records(buffer)
            if save_batch_fn:
                save_batch_fn(df, {"collected": collected_total})
            if self.cp:
                self.cp.add_seen([x["post_id"] for x in buffer])
            yield df, {"collected": collected_total}
