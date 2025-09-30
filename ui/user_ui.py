import streamlit as st
from services.twitter_playwright import PlaywrightTwitterScraper
from utils.io import df_to_csv_bytes
from storage.db import save_records

def render_user_tab(cookie_meta):
    st.header("👤 Crawl User Timeline")

    username = st.text_input("Nhập username (không có @)", value="elonmusk", key="user_username")
    max_posts = st.number_input("Số lượng tối đa", min_value=10, max_value=2000, value=100, step=50, key="user_max")
    headless = st.checkbox("Headless", value=True, key="user_headless")

    if st.button("🚀 Start Crawl User", key="user_btn"):
        scraper = PlaywrightTwitterScraper(headless=headless, cookies_path=cookie_meta.get("cookies_path"))
        dfs = []
        for df, meta in scraper.user_tweets(username, limit=max_posts):
            dfs.append(df)

        if not dfs:
            st.warning("❌ Không thu được dữ liệu.")
            return

        final_df = dfs[-1]
        st.success(f"✅ Thu được {len(final_df)} bài viết từ @{username}")
        st.dataframe(final_df)

        # Xuất CSV
        csv_bytes = df_to_csv_bytes(final_df)
        st.download_button("📥 Download CSV", data=csv_bytes, file_name=f"{username}_tweets.csv", mime="text/csv")

        # Lưu DB
        save_records(final_df, table_name="tweets")
        st.info("💾 Dữ liệu đã lưu vào MySQL")
