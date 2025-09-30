import re
from typing import Optional, Dict, List

_KEYWORDS = {
    "reply": ["reply", "replies", "trả lời"],
    "like": ["like", "likes", "thích"],
    "view": ["view", "views", "lượt xem", "xem"],
    "repost": ["repost", "reposts", "retweet", "retweets", "chia sẻ"],
}

def parse_metrics_from_aria(aria: Optional[str]) -> Dict[str, Optional[int]]:
    out: Dict[str, Optional[int]] = {"reply_count": None, "like_count": None, "view_count": None, "repost_count": None}
    if not aria:
        return out
    for part in aria.lower().split(","):
        part = part.strip()
        m = re.search(r"(\d[\d,\.]*)", part)
        if not m:
            continue
        n = int(re.sub(r"[,\.\s]", "", m.group(1)))
        if any(k in part for k in _KEYWORDS["reply"]):
            out["reply_count"] = n
        elif any(k in part for k in _KEYWORDS["like"]):
            out["like_count"] = n
        elif any(k in part for k in _KEYWORDS["view"]):
            out["view_count"] = n
        elif any(k in part for k in _KEYWORDS["repost"]):
            out["repost_count"] = n
    return out

def normalize_cookies(cookies: List[dict]) -> List[dict]:
    valid = {"Strict", "Lax", "None"}
    for c in cookies:
        if "sameSite" not in c or c["sameSite"] not in valid:
            c["sameSite"] = "Lax"
    return cookies

def post_id_from_href(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    m = re.search(r"/status/(\d+)", href)
    return m.group(1) if m else None
