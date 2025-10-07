import streamlit as st
import json, os
from utils.io import save_temp_json

COOKIE_TMP_DIR = "cookies"

def render_sidebar():
    st.sidebar.header("⚙️ Global Config")

    # ===================================================
    #  ACCOUNTS CONFIGURATION
    # ===================================================
    st.sidebar.subheader("👥 Accounts Configuration")

    if "accounts" not in st.session_state:
        st.session_state["accounts"] = [{
            "cookie_path": "",
            "bearer": ""
        }]

    accounts = st.session_state["accounts"]

    for i, acc in enumerate(accounts):
        st.sidebar.markdown(f"### 🔹 Account {i + 1}")

        # ---- Cookie (upload or paste)
        cookie_file = st.sidebar.file_uploader(
            f"Cookie JSON file (Account {i+1})",
            type="json",
            key=f"cookie_upload_{i}"
        )
        cookie_path = ""
        if cookie_file:
            os.makedirs(COOKIE_TMP_DIR, exist_ok=True)
            dest = os.path.join(COOKIE_TMP_DIR, f"acc{i+1}_{cookie_file.name}")
            with open(dest, "wb") as out:
                out.write(cookie_file.read())
            cookie_path = dest
        else:
            pasted = st.sidebar.text_area(
                f"Or paste cookie JSON (Account {i+1})",
                height=100,
                key=f"cookie_paste_{i}"
            )
            if pasted:
                try:
                    data = json.loads(pasted)
                    os.makedirs(COOKIE_TMP_DIR, exist_ok=True)
                    dest = os.path.join(COOKIE_TMP_DIR, f"acc{i+1}_pasted.json")
                    save_temp_json(data, dest)
                    cookie_path = dest
                    st.sidebar.success(f"✅ Saved cookie for Account {i+1}")
                except Exception:
                    st.sidebar.error("❌ Invalid JSON cookie")

        bearer = st.sidebar.text_input(
            f"Bearer Token (Account {i+1})",
            type="password",
            key=f"bearer_{i}"
        )

        acc["cookie_path"] = cookie_path or acc.get("cookie_path", "")
        acc["bearer"] = bearer

        st.sidebar.markdown("---")

    # ---- Add account button
    if st.sidebar.button("➕ Add account"):
        accounts.append({
            "cookie_path": "",
            "bearer": ""
        })

    # ===================================================
    #  🌐 PROXY POOL (updated to dynamic add/remove)
    # ===================================================
    st.sidebar.subheader("🌐 Proxy Pool (optional)")

    if "proxies" not in st.session_state:
        st.session_state["proxies"] = []

    remove_idxs = []
    for i, proxy in enumerate(st.session_state["proxies"]):
        cols = st.sidebar.columns([4, 1])
        with cols[0]:
            st.session_state["proxies"][i] = st.text_input(
                f"Proxy #{i+1}",
                value=proxy,
                key=f"proxy_{i}",
                placeholder="http://user:pass@ip:port hoặc socks5://ip:port"
            )
        with cols[1]:
            if st.button("❌", key=f"remove_proxy_{i}"):
                remove_idxs.append(i)

    for idx in sorted(remove_idxs, reverse=True):
        del st.session_state["proxies"][idx]

    if st.sidebar.button("➕ Add proxy"):
        st.session_state["proxies"].append("")

    if st.session_state["proxies"]:
        st.sidebar.markdown("**Danh sách Proxy hiện tại:**")
        for p in st.session_state["proxies"]:
            st.sidebar.write(f"🔹 {p or '(chưa nhập)'}")
    else:
        st.sidebar.info("Chưa có proxy nào được cấu hình.")

    proxies = [p for p in st.session_state["proxies"] if p.strip()]

    # ===================================================
    #  GLOBAL GRAPHQL KEYS
    # ===================================================
    st.sidebar.subheader("🔑 Global GraphQL Keys (used for all accounts)")
    gql_result_global = st.sidebar.text_input(
        "GraphQL key - TweetResultByRestId",
        key="gql_result_global"
    )
    gql_detail_global = st.sidebar.text_input(
        "GraphQL key - TweetDetail",
        key="gql_detail_global"
    )

    # ===================================================
    #  INIT DB BUTTON
    # ===================================================
    if st.sidebar.button("🗄️ Init DB schema", key="init_db_btn"):
        st.session_state["_do_init_db"] = True

    # ===================================================
    #  RETURN CONFIG
    # ===================================================
    return {
        "accounts": accounts,
        "proxies": proxies,
        "gql_result_global": gql_result_global,
        "gql_detail_global": gql_detail_global
    }
