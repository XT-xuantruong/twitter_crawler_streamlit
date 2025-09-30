import streamlit as st
import os, json

COOKIE_TMP = "tmp_cookies_shared.json"

def render_sidebar():
    st.sidebar.header("⚙️ Config chung")

    cookie_mode = st.sidebar.radio("Cookie input", ["Path", "Upload", "Paste"], index=0)
    cookies_path = None

    if cookie_mode == "Path":
        cookies_path = st.sidebar.text_input("Cookies JSON path", value="cookies.json")
    elif cookie_mode == "Upload":
        uploaded = st.sidebar.file_uploader("Upload cookies.json", type="json")
        if uploaded:
            cookies_path = COOKIE_TMP
            with open(cookies_path, "wb") as f:
                f.write(uploaded.read())
            st.sidebar.success(f"Saved temporary cookies: {cookies_path}")
    else:
        pasted = st.sidebar.text_area("Paste cookies JSON", height=120)
        if pasted:
            try:
                data = json.loads(pasted)
                cookies_path = COOKIE_TMP
                with open(cookies_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                st.sidebar.success(f"Saved temporary cookies: {cookies_path}")
            except Exception:
                st.sidebar.error("Invalid JSON")

    st.sidebar.caption("Nếu cookie hết hạn, export lại từ trình duyệt rồi upload/paste vào đây.")
    return {"cookies_path": cookies_path}
