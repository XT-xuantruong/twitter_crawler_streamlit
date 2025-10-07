import re
from typing import Optional, Dict, Any, List

_KEYWORDS = {
    "reply": ["reply", "replies", "trả lời"],
    "like": ["like", "likes", "thích"],
    "view": ["view", "views", "lượt xem", "xem"],
    "repost": ["repost", "reposts", "retweet", "retweets", "chia sẻ"],
}

def parse_metrics_from_aria(aria: Optional[str]) -> Dict[str, Optional[int]]:
    if not aria:
        return {"reply_count": None, "like_count": None, "view_count": None, "repost_count": None}
    lower = aria.lower()
    out = {"reply_count": None, "like_count": None, "view_count": None, "repost_count": None}
    parts = [p.strip() for p in lower.split(",")]
    for p in parts:
        m = re.search(r"(\d[\d,\.]*)", p)
        if not m:
            continue
        n_raw = m.group(1)
        n = int(re.sub(r"[,\.\s]", "", n_raw))
        if any(k in p for k in _KEYWORDS["reply"]):
            out["reply_count"] = n # type: ignore
        elif any(k in p for k in _KEYWORDS["like"]):
            out["like_count"] = n # type: ignore
        elif any(k in p for k in _KEYWORDS["view"]):
            out["view_count"] = n # type: ignore
        elif any(k in p for k in _KEYWORDS["repost"]):
            out["repost_count"] = n # type: ignore
    return out

def normalize_cookies(cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid_values = {"Strict", "Lax", "None"}
    for c in cookies:
        if "sameSite" not in c or c["sameSite"] not in valid_values:
            c["sameSite"] = "Lax"
    return cookies

def post_id_from_href(href: Optional[str]) -> Optional[str]:
    if not href: return None
    m = re.search(r"/status/(\d+)", href)
    return m.group(1) if m else None
