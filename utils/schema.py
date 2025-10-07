from typing import List, Dict, Any
import pandas as pd

TWEET_COLUMNS = [
    "post_id","created_at","text",
    "user_id","username","displayname","verified_flag",
    "followers_count","friends_count","statuses_count",
    "like_count","retweet_count","reply_count","quote_count",
    "hashtags","urls","link","view_count"
]

REPLY_COLUMNS = [
    "reply_id","post_id","created_at","text",
    "user_id","username","displayname","verified_flag",
    "like_count","reply_count","retweet_count"
]

def normalize_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    for col in TWEET_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[TWEET_COLUMNS] # type: ignore

def normalize_replies(records: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    for col in REPLY_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[REPLY_COLUMNS] # type: ignore
