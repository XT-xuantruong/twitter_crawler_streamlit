import pandas as pd
from storage import db
from dotenv import load_dotenv
import os
# load_dotenv()

def main():
    print(">>> Loading .env ...")
    loaded = load_dotenv()
    print(">>> load_dotenv result:", loaded)
    print(os.getenv("MSSQL_URL"))
    # Dữ liệu mẫu
    data = [
        {
            "post_id": "1234567890",
            "platform": "twitter",
            "text": "This is a fake news test post 🚀",
            "language": "en",
            "created_at": "2025-09-30 12:00:00",
            "username": "tester",
            "like_count": 10,
            "retweet_count": 2,
            "reply_count": 1,
            "quote_count": 0,
            "link": "https://x.com/tester/status/1234567890"
        },
        {
            "post_id": "9876543210",
            "platform": "twitter",
            "text": "Second sample tweet 👍",
            "language": "vi",
            "created_at": "2025-09-30 13:00:00",
            "username": "tester2",
            "like_count": 5,
            "retweet_count": 0,
            "reply_count": 0,
            "quote_count": 0,
            "link": "https://x.com/tester2/status/9876543210"
        }
    ]

    df = pd.DataFrame(data)

    print("🚀 Bắt đầu test lưu MySQL...")
    db.save_records(df, table_name="tweets")
    print("✅ Test lưu dữ liệu xong!")

if __name__ == "__main__":
    main()
