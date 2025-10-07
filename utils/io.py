import os, json
import pandas as pd
from datetime import datetime
from typing import Dict

def _ts() -> str:
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def export_csv(df: pd.DataFrame, out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"social_posts_{_ts()}.csv")
    df.to_csv(path, index=False)
    return path

def save_temp_json(obj: Dict, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
