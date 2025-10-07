import streamlit as st
import pandas as pd
from storage.db import get_engine

def render_dashboard_tab(cfg):
    st.header("📊 Crawl Dashboard")

    engine = get_engine()
    with engine.connect() as conn:
        tweets = pd.read_sql("SELECT TOP 50 * FROM tweets ORDER BY created_at DESC", conn)
        replies = pd.read_sql("SELECT TOP 50 * FROM tweet_replies ORDER BY created_at DESC", conn)
        if tweets.empty and replies.empty:
            st.info("No data available. Please run a crawl to fetch tweets and replies.")
            return

    st.subheader("🧵 Latest Tweets")
    st.dataframe(tweets)

    st.subheader("💬 Latest Replies")
    st.dataframe(replies)
