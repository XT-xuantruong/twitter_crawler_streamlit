import streamlit as st
import pandas as pd
from services.controller import TwitterCrawlerController
from storage.db import init_db

def render_search_tab(cfg):
    st.header("🔍 Twitter Search Crawler")

    query = st.text_input("Search query", placeholder="fake news, scam, AI, ...")
    limit = st.number_input("Limit", min_value=10, max_value=1000, value=100, step=10)
    start_btn = st.button("🚀 Start Crawl")

    # chọn tài khoản đang dùng (optional)
    acc_names = [f"Account #{i+1}" for i in range(len(cfg["accounts"]))]
    selected_acc = st.selectbox("Select account (optional)", ["Auto Rotate"] + acc_names)

    if start_btn:
        if not query.strip():
            st.warning("Please enter a search query.")
            return

        init_db()
        st.info(f"Starting search for **{query}** ...")

        # chuẩn bị list accounts
        accounts = cfg["accounts"]
        controller = TwitterCrawlerController(cfg)

        controller.run_full_pipeline(query, limit=limit)
        st.success("✅ Crawl completed successfully!")
