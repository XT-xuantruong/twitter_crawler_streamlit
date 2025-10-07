import pandas as pd
import time, logging, traceback
from queue import Queue
from typing import Dict, Any

from services.twitter_playwright import PlaywrightTwitterScraper
from services.twitter_graphql import fetch_tweet_detail
from services.parser_tweet_detail import parse_tweet_detail_full
from services.cookies_manager import CookiesManager
from storage.db import save_records, init_db


# ===============================================================
# LOGGING
# ===============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TwitterCrawler")


# ===============================================================
# CONTROLLER CLASS
# ===============================================================
class TwitterCrawlerController:
    def __init__(self, config: dict):
        self.config = config
        self.accounts = config.get("accounts", [])
        self.gql_detail_key = config.get("gql_detail_key", "")
        self.cookies_mgr = None
        self.account_index = 0
        self.auto_rotate = True
        self.retry_queue = Queue()
        self.max_retry = 3
        self.rate_limit_hits = 0
        self.cooldown_time = 15 * 60  # 15 phút cooldown khi hết tài khoản

        # Bộ nhớ tạm để lưu dữ liệu trước cooldown
        self._pending_tweets = []
        self._pending_replies = []

        if not self.accounts:
            raise ValueError("❌ No accounts configured in sidebar!")

        # khởi tạo account đầu tiên
        self._set_current_account(0)

    # ===========================================================
    # ACCOUNT MANAGEMENT
    # ===========================================================
    def _set_current_account(self, index: int):
        if index >= len(self.accounts):
            index = 0
        self.account_index = index
        acc = self.accounts[index]
        logger.info(f"👉 Using Account #{index + 1} (cookie={acc.get('cookie_path')})")

        self.cookies_mgr = CookiesManager([acc["cookie_path"]])
        self.bearer = acc.get("bearer", "")

    def _rotate_account(self):
        """Switch to next account; if all exhausted → enter cooldown"""
        if not self.auto_rotate or len(self.accounts) <= 1:
            return False

        self.account_index = (self.account_index + 1) % len(self.accounts)
        acc = self.accounts[self.account_index]
        logger.warning(f"⚠️ Switching to Account #{self.account_index + 1} due to error...")
        self._set_current_account(self.account_index)
        time.sleep(3)

        # Đếm xem đã xoay hết vòng chưa
        self.rate_limit_hits += 1
        if self.rate_limit_hits >= len(self.accounts):
            logger.error("🚫 All accounts are rate-limited! Entering cooldown mode...")

            # 🧩 SAVE PROGRESS trước khi nghỉ cooldown
            try:
                if self._pending_tweets:
                    df_tweets = pd.DataFrame(self._pending_tweets)
                    save_records(df_tweets, "tweets")
                    logger.info(f"💾 Auto-saved {len(df_tweets)} pending tweets before cooldown.")
                    self._pending_tweets.clear()

                if self._pending_replies:
                    df_replies = pd.DataFrame(self._pending_replies)
                    save_records(df_replies, "tweet_replies")
                    logger.info(f"💬 Auto-saved {len(df_replies)} pending replies before cooldown.")
                    self._pending_replies.clear()
            except Exception as e:
                logger.error(f"❌ Failed to save pending data before cooldown: {e}")

            # 💤 Cooldown nghỉ
            logger.warning(f"⏳ Cooling down for {self.cooldown_time / 60:.0f} minutes...")
            time.sleep(self.cooldown_time)
            self.rate_limit_hits = 0
            return False
        return True

    # ===========================================================
    # MAIN PIPELINE
    # ===========================================================
    def run_full_pipeline(self, query: str, limit: int = 300, batch_size: int = 100):
        """Run full crawler pipeline: search → GraphQL enrich → save"""
        init_db()
        logger.info(f"🚀 Starting crawl for query: {query}")

        scraper = PlaywrightTwitterScraper(
            headless=True,
            cookies_path=self.accounts[self.account_index]["cookie_path"],
            checkpoint_path="checkpoint.json"
        )

        try:
            for df, meta in scraper.search(query, limit=limit, batch_size=batch_size):
                logger.info(f"📦 Batch collected: {len(df)} tweets | Total: {meta['collected']}")
                save_records(df, "tweets")
                self._process_graphql_batch(df)
        finally:
            scraper.close()

        self._process_retry_queue()
        logger.info("✅ Pipeline completed successfully.")

    # ===========================================================
    # GRAPHQL DETAIL ENRICHMENT
    # ===========================================================
    def _process_graphql_batch(self, df: pd.DataFrame):
        tweets_to_update, replies_to_save = [], []

        for _, row in df.iterrows():
            tid = str(row["post_id"])
            try:
                data = fetch_tweet_detail(
                    tid,
                    self.cookies_mgr,
                    bearer=self.bearer,
                    gql_key=self.gql_detail_key
                )
                main_tweet, replies = parse_tweet_detail_full(data)

                if main_tweet:
                    tweets_to_update.append(main_tweet)
                    self._pending_tweets.append(main_tweet)
                if replies:
                    replies_to_save.extend(replies)
                    self._pending_replies.extend(replies)

                logger.info(f"🧩 Enriched {tid} — {len(replies)} replies")

            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["403", "429", "auth"]):
                    logger.error(f"[RateLimit/Auth] {tid}: {e}")
                    rotated = self._rotate_account()
                    if not rotated:
                        # Cooldown kích hoạt → flush dữ liệu tạm
                        if tweets_to_update:
                            save_records(pd.DataFrame(tweets_to_update), "tweets")
                            tweets_to_update.clear()
                        if replies_to_save:
                            save_records(pd.DataFrame(replies_to_save), "tweet_replies")
                            replies_to_save.clear()
                        logger.warning("🕒 Cooldown active, pausing enrichment temporarily...")
                        return
                else:
                    logger.error(f"[GraphQL ERROR] {tid}: {e}")
                    self.retry_queue.put({"tweet_id": tid, "attempts": 1})
                continue

        # ✅ SAVE batch hiện tại
        if tweets_to_update:
            save_records(pd.DataFrame(tweets_to_update), "tweets")
            logger.info(f"💾 Updated {len(tweets_to_update)} tweets")

        if replies_to_save:
            save_records(pd.DataFrame(replies_to_save), "tweet_replies")
            logger.info(f"💬 Saved {len(replies_to_save)} replies")

    # ===========================================================
    # RETRY QUEUE HANDLER
    # ===========================================================
    def _process_retry_queue(self):
        if self.retry_queue.empty():
            return
        logger.warning(f"🔁 Retrying {self.retry_queue.qsize()} failed tweets...")

        all_retries = []
        while not self.retry_queue.empty():
            item = self.retry_queue.get()
            tid = item["tweet_id"]
            attempts = item["attempts"]

            try:
                data = fetch_tweet_detail(
                    tid,
                    self.cookies_mgr,
                    bearer=self.bearer,
                    gql_key=self.gql_detail_key
                )
                main_tweet, replies = parse_tweet_detail_full(data)
                if main_tweet:
                    all_retries.append(main_tweet)
                if replies:
                    save_records(pd.DataFrame(replies), "tweet_replies")
                logger.info(f"✅ Retry success: {tid}")

            except Exception as e:
                if any(x in str(e) for x in ["403", "429"]):
                    logger.warning(f"Rate limit in retry: rotating account...")
                    rotated = self._rotate_account()
                    if not rotated:
                        logger.warning("🕒 Cooldown active during retry...")
                        break
                    self.retry_queue.put({"tweet_id": tid, "attempts": attempts})
                    continue
                if attempts < self.max_retry:
                    self.retry_queue.put({"tweet_id": tid, "attempts": attempts + 1})
                else:
                    logger.error(f"❌ Retry limit reached for {tid}: {e}")
                continue

        if all_retries:
            save_records(pd.DataFrame(all_retries), "tweets")
            logger.info(f"💾 Saved {len(all_retries)} tweets from retry queue")
