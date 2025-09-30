import streamlit as st
import os, json, uuid

def render_sidebar():
    # đảm bảo mỗi session có id riêng
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    session_id = st.session_state["session_id"]
    COOKIE_TMP = f"tmp_cookies_{session_id}.json"
    st.sidebar.header("⚙️ Common Config")

    cookie_mode = st.sidebar.radio("Cookie input", ["Upload", "Paste"], index=0)
    # auto gán file theo session_id
    cookies_path = f"tmp_cookies_{st.session_state.session_id}.json"

    if cookie_mode == "Upload":
        uploaded = st.sidebar.file_uploader("Upload cookies.json", type="json")
        if uploaded:
            with open(cookies_path, "wb") as f:
                f.write(uploaded.read())
            st.sidebar.success(f"✅ Saved cookies for this session: {cookies_path}")

    else:  # Paste
        pasted = st.sidebar.text_area("Paste cookies JSON", height=120)
        if pasted:
            try:
                data = json.loads(pasted)
                with open(cookies_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                st.sidebar.success(f"✅ Saved cookies for this session: {cookies_path}")
            except Exception:
                st.sidebar.error("❌ Invalid JSON")

    st.sidebar.caption("If cookie expires, please export again from your browser and re-upload/paste.")
    return {"cookies_path": cookies_path}
