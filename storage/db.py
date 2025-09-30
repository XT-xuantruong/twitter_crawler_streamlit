import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load .env nếu có
load_dotenv()

MSSQL_URL = os.environ.get("MSSQL_URL")

if not MSSQL_URL:
    raise RuntimeError("❌ MSSQL_URL not found. Check your .env file!")

# Tạo engine
engine = create_engine(MSSQL_URL, pool_pre_ping=True, future=True)

# DDL tạo bảng tweets
DDL_TWEETS = """
CREATE TABLE IF NOT EXISTS tweets (
    post_id VARCHAR(64) PRIMARY KEY,
    platform VARCHAR(50),
    text TEXT,
    language VARCHAR(10),
    created_at DATETIME,
    username VARCHAR(255),
    like_count INT,
    retweet_count INT,
    reply_count INT,
    quote_count INT,
    link VARCHAR(512)
) CHARACTER SET utf8mb4;
"""

def init_db():
    """Đảm bảo bảng tồn tại"""
    try:
        with engine.begin() as conn:
            conn.execute(text(DDL_TWEETS))
        print("✅ Database initialized and table ensured.")
    except OperationalError as e:
        print(f"❌ Cannot connect to MySQL: {e}")
        raise

def save_records(df: pd.DataFrame, table_name: str = "tweets"):
    if df is None or df.empty:
        return

    # 🔥 Convert NaN → None để MySQL nhận dạng là NULL
    df = df.replace({np.nan: None})

    rows = df.to_dict(orient="records")

    with engine.begin() as conn:
        for r in rows:
            conn.execute(text(f"""
                INSERT INTO {table_name} (post_id, platform, text, language, created_at, username,
                                          like_count, retweet_count, reply_count, quote_count, link)
                VALUES (:post_id, :platform, :text, :language, :created_at, :username,
                        :like_count, :retweet_count, :reply_count, :quote_count, :link)
                ON DUPLICATE KEY UPDATE
                    text = VALUES(text),
                    like_count = VALUES(like_count),
                    retweet_count = VALUES(retweet_count),
                    reply_count = VALUES(reply_count),
                    quote_count = VALUES(quote_count);
            """), r)