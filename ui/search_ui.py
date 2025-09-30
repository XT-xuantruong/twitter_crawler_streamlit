import streamlit as st
from services.twitter_playwright import PlaywrightTwitterScraper
from utils.io import df_to_csv_bytes
from storage.db import save_records

def render_search_tab(cookie_meta):
    st.header("🔍 Twitter Search")

    query = st.text_input("Nhập từ khoá tìm kiếm", value="fake news", key="search_query")
    max_posts = st.number_input("Số lượng tối đa", min_value=10, max_value=2000, value=100, step=50, key="search_max")
    headless = st.checkbox("Headless", value=True, key="search_headless")

    if st.button("🚀 Start Search", key="search_btn"):
        print("Starting search with cookie:", cookie_meta.get("cookies_path"))
        scraper = PlaywrightTwitterScraper(headless=headless, cookies_path=cookie_meta.get("cookies_path"))
        dfs = []
        for df, meta in scraper.search(query, limit=max_posts):
            dfs.append(df)

        if not dfs:
            st.warning("❌ Không thu được dữ liệu.")
            return

        final_df = dfs[-1]
        st.success(f"✅ Thu được {len(final_df)} bài viết.")
        st.dataframe(final_df)

        # Xuất CSV
        csv_bytes = df_to_csv_bytes(final_df)
        st.download_button("📥 Download CSV", data=csv_bytes, file_name="tweets_search.csv", mime="text/csv")

        # Lưu DB
        save_records(final_df, table_name="tweets")
        st.info("💾 Dữ liệu đã lưu vào MySQL")
