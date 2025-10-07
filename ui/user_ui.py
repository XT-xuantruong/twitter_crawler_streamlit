# import streamlit as st
# import pandas as pd
# from services.twitter_playwright import PlaywrightTwitterScraper
# from storage.db import save_records
# from utils.schema import normalize_records
# from utils.io import df_to_csv_bytes
# from storage.db import init_db

# def render_user_tab(config):
#     st.header("👤 Crawl User Timeline")
#     username = st.text_input("Username (without @)", key="user_username")
#     max_posts = st.number_input("Max posts", min_value=10, max_value=50000, value=500, step=50, key="user_max_posts")
#     headless = st.checkbox("Headless", value=True, key="user_headless")
#     if st.button("Start User Crawl", key="start_user_btn"):
#         init_db()
#         scraper = PlaywrightTwitterScraper(headless=headless, cookies_path=(config["cookie_paths"][0] if config["cookie_paths"] else None))
#         all_dfs = []
#         try:
#             for df, meta in scraper.user_tweets(username, limit=max_posts, batch_size=100):
#                 st.write(f"Batch {len(df)} — total {meta.get('collected')}")
#                 all_dfs.append(df)
#                 save_records(df, table="tweets")
#             if not all_dfs:
#                 st.warning("No tweets collected")
#             else:
#                 final_df = pd.concat(all_dfs, ignore_index=True)
#                 st.success(f"Collected {len(final_df)} tweets (saved to DB)")
#                 st.dataframe(final_df.head(50))
#                 st.download_button("Download CSV", data=df_to_csv_bytes(final_df), file_name="user_tweets.csv", mime="text/csv", key="download_user_csv")
#         finally:
#             scraper.close()
