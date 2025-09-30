import streamlit as st
import pandas as pd
from sqlalchemy import text
from storage.db import engine

def render_dashboard_tab(cookie_meta=None):
    st.header("📊 Dashboard")

    # Bộ lọc
    keyword = st.text_input("🔍 Tìm theo keyword", value="", key="dash_keyword")
    start_date = st.date_input("Từ ngày", key="dash_start")
    end_date = st.date_input("Đến ngày", key="dash_end")

    query = "SELECT * FROM tweets WHERE 1=1"
    params = {}

    if keyword:
        query += " AND text LIKE :kw"
        params["kw"] = f"%{keyword}%"

    if start_date:
        query += " AND created_at >= :start"
        params["start"] = str(start_date)

    if end_date:
        query += " AND created_at <= :end"
        params["end"] = str(end_date)

    with engine.begin() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    if df.empty:
        st.warning("❌ Không có dữ liệu.")
        return

    # Hiển thị bảng với phân trang
    st.write("### 📋 Kết quả")
    st.dataframe(df)

    # Thống kê đơn giản
    st.write("### 📈 Thống kê")
    st.metric("Tổng số bài viết", len(df))
    st.bar_chart(df["language"].value_counts())

    if "like_count" in df:
        st.bar_chart(df.groupby("language")["like_count"].sum())
