import streamlit as st
from ui.sidebar_ui import render_sidebar
from ui.search_ui import render_search_tab
from ui.dashboard_ui import render_dashboard_tab
from storage.db import init_db
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="X/Twitter Crawler", layout="wide")
st.title("X/Twitter Crawler Platform")

config = render_sidebar()

cfg = {
    "accounts": config["accounts"],  # list[{cookie_path, bearer}]
    "proxies": config["proxies"],
    "gql_result_key": config["gql_result_global"],
    "gql_detail_key": config["gql_detail_global"]
}

tabs = st.tabs(["🔍 Search", "📊 Dashboard"])
with tabs[0]:
    render_search_tab(cfg)
with tabs[1]:
    render_dashboard_tab(cfg)

# init DB if requested
if st.session_state.get("_do_init_db"):
    init_db()
    st.success("DB initialized")
    st.session_state["_do_init_db"] = False
