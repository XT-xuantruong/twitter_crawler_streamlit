import os
import json
import pandas as pd
from datetime import datetime

def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Chuyển DataFrame thành CSV bytes để streamlit download"""
    return df.to_csv(index=False).encode("utf-8")

def export_csv(df: pd.DataFrame, out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"social_posts_{_ts()}.csv")
    df.to_csv(path, index=False)
    return path

def export_jsonl(df: pd.DataFrame, out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"social_posts_{_ts()}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            f.write(json.dumps(row.dropna().to_dict(), ensure_ascii=False) + "\n")
    return path
