import os

class Config:
    # MySQL URL (đổi theo môi trường của bạn)
    # ví dụ: mysql+pymysql://user:pass@localhost:3306/social_crawler?charset=utf8mb4
    MSSQL_URL = os.environ.get(
        "MSSQL_URL"
        # "mysql+pymysql://root:password@localhost:3306/social_crawler?charset=utf8mb4"
    )

    # user-agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    # timings
    SCROLL_DELAY = (1.0, 2.2)
    FIRST_LOAD_DELAY = (2.0, 3.0)
    STAGNATION_LIMIT = 8

    # crawl defaults
    BATCH_SIZE = 200
    DEFAULT_LIMIT = 1000
    DEFAULT_LANG = "en"
