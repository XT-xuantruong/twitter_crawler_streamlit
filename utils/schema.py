import pandas as pd
from typing import List, Dict, Any

CANONICAL_COLS = [
    "platform","post_id","created_at","language","text",
    "user_id","username","displayname","verified_flag",
    "followers_count","friends_count","statuses_count",
    "like_count","retweet_count","reply_count","quote_count",
    "hashtags","urls","link","view_count"
]

def normalize_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=CANONICAL_COLS)
    df = pd.DataFrame(records)
    for c in CANONICAL_COLS:
        if c not in df.columns:
            df[c] = None
    result = df.loc[:, CANONICAL_COLS]
    if isinstance(result, pd.Series):
        result = result.to_frame().T
    return result
