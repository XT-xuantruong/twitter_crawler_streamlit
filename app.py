import streamlit as st
from ui.sidebar_ui import render_sidebar
from ui.search_ui import render_search_tab
from ui.user_ui import render_user_tab
from ui.dashboard_ui import render_dashboard_tab
import os
from dotenv import load_dotenv
load_dotenv()


st.set_page_config(page_title="Twitter/X Crawler — Playwright", layout="wide")
st.title("📡 Twitter/x Crawler — Playwright")

cookie_meta = render_sidebar()

tabs = st.tabs(["📊 Dashboard","🔍 Search by query", "👤 Search by user"])
with tabs[0]:
    render_dashboard_tab(cookie_meta)
with tabs[1]:
    render_search_tab(cookie_meta)
with tabs[2]:
    render_user_tab(cookie_meta)
