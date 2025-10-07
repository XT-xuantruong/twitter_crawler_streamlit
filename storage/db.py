from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from urllib.parse import quote_plus
from core.config import Config

TABLE_TWEETS = "tweets"
TABLE_REPLIES = "tweet_replies"

# =============================================================
#  SCHEMA DEFINITIONS (SQL SERVER)
# =============================================================
DDL_TWEETS = f"""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{TABLE_TWEETS}' AND xtype='U')
BEGIN
    CREATE TABLE {TABLE_TWEETS} (
        post_id VARCHAR(64) PRIMARY KEY,
        user_id VARCHAR(64),
        username NVARCHAR(255),
        displayname NVARCHAR(255),
        is_blue_verified BIT,
        favourites_count INT,
        followers_count INT,
        friends_count INT,
        listed_count INT,
        media_count INT,
        created_at DATETIME NULL,
        full_text NVARCHAR(MAX),
        quote_count INT,
        reply_count INT,
        retweet_count INT,
        like_count INT,
        view_count INT,
        lang NVARCHAR(10),
        link NVARCHAR(512)
    )
END
"""

DDL_REPLIES = f"""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{TABLE_REPLIES}' AND xtype='U')
BEGIN
    CREATE TABLE {TABLE_REPLIES} (
        reply_id VARCHAR(64) PRIMARY KEY,
        post_id VARCHAR(64),
        created_at DATETIME NULL,
        text NVARCHAR(MAX),
        user_id VARCHAR(64),
        username NVARCHAR(255),
        displayname NVARCHAR(255),
        verified_flag BIT,
        like_count INT,
        reply_count INT,
        retweet_count INT,
        quote_count INT,
        followers_count INT,
        friends_count INT,
        favourites_count INT,
        media_count INT,
        view_count INT,
        lang NVARCHAR(10),
        FOREIGN KEY (post_id) REFERENCES {TABLE_TWEETS}(post_id)
    )
END
"""

# =============================================================
#  ENGINE INITIALIZATION
# =============================================================
def get_engine():

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=27.71.106.203,1433;"
        "DATABASE=FK_DB;"
        "UID=sa;"
        "PWD=@AbcTamky123;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    params = quote_plus(conn_str)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", pool_pre_ping=True, fast_executemany=True)
    return engine


def init_db():
    """Khởi tạo bảng nếu chưa có"""
    engine = get_engine()
    with engine.begin() as conn:
        print("🗄️  Initializing database tables if not exist...")
        conn.execute(text(DDL_TWEETS))
        conn.execute(text(DDL_REPLIES))
        # Đảm bảo cột view_count tồn tại (trường hợp bảng cũ)
        conn.execute(text("""
            IF COL_LENGTH('dbo.tweets', 'view_count') IS NULL
                ALTER TABLE dbo.tweets ADD view_count INT NULL;
        """))
        conn.execute(text("""
            IF COL_LENGTH('dbo.tweet_replies', 'view_count') IS NULL
                ALTER TABLE dbo.tweet_replies ADD view_count INT NULL;
        """))
        print("✅ Database schema check complete.")


# =============================================================
#  SAVE / UPSERT
# =============================================================
def _to_sql_val(v):
    """Chuyển NaN → None"""
    if pd.isnull(v):
        return None
    return v


def save_records(df: pd.DataFrame, table: str):
    """Upsert records (INSERT or UPDATE nếu tồn tại)"""
    if df is None or df.empty:
        return

    engine = get_engine()
    with engine.begin() as conn:
        for _, row in df.iterrows():
            data = {k: _to_sql_val(v) for k, v in row.to_dict().items()}
            if "post_id" in data:
                key_col = "post_id"
            elif "reply_id" in data:
                key_col = "reply_id"
            else:
                continue

            # ========== MERGE SQL SERVER ==========
            cols = ", ".join(f"[{k}]" for k in data.keys())
            vals = ", ".join(f":{k}" for k in data.keys())
            updates = ", ".join(f"T.[{k}] = S.[{k}]" for k in data.keys() if k != key_col)

            sql = f"""
            MERGE {table} AS T
            USING (SELECT {', '.join(f':{k} AS [{k}]' for k in data.keys())}) AS S
            ON (T.[{key_col}] = S.[{key_col}])
            WHEN MATCHED THEN UPDATE SET {updates}
            WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({vals});
            """
            try:
                conn.execute(text(sql), data)
            except SQLAlchemyError as e:
                print(f"[DB ERROR] {e}")
