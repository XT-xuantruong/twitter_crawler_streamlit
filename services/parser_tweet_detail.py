"""
Parse GraphQL TweetDetail JSON → (tweet_main, replies[])
"""

from typing import Tuple, Dict, Any, List, Optional


def parse_tweet_detail_full(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse full tweet + replies from TweetDetail GraphQL JSON"""
    main_tweet: Dict[str, Any] = {}
    replies: List[Dict[str, Any]] = []

    instructions = data.get("data", {}).get("threaded_conversation_with_injections", {}).get("instructions", [])
    for inst in instructions:
        entries = inst.get("entries", [])
        for entry in entries:
            entry_id = entry.get("entryId", "")

            # ===================== MAIN TWEET =====================
            if entry_id.startswith("tweet-"):
                content = entry.get("content", {}).get("itemContent", {})
                tweet = _extract_tweet_item(content)
                if tweet:
                    # tweet gốc: chuyển reply_id -> post_id nếu cần
                    if tweet.get("reply_id") and not tweet.get("post_id"):
                        tweet["post_id"] = tweet["reply_id"]
                    # tweet gốc không cần reply_id
                    tweet.pop("reply_id", None)
                    main_tweet = tweet

            # ====================== REPLIES =======================
            elif entry_id.startswith("conversationthread-"):
                items = entry.get("content", {}).get("items", [])
                for it in items:
                    ic = it.get("item", {}).get("itemContent", {})
                    reply = _extract_tweet_item(ic)
                    if reply:
                        # đảm bảo có post_id là id của tweet gốc (conversation_id_str)
                        if not reply.get("post_id"):
                            reply["post_id"] = main_tweet.get("post_id")
                        replies.append(reply)

    return main_tweet, replies


def _extract_view_count(res: Dict[str, Any]) -> Optional[int]:
    """
    Twitter GraphQL có nhiều nhánh khác nhau cho views:
    - res["views"]["count"]
    - res["legacy"]["views"]["count"]
    - res["ext_views"]["count"]
    - res["legacy"]["ext_views"]["count"]
    → Hàm này gom tất cả các khả năng và trả về int hoặc None.
    """
    paths = [
        ("views", "count"),
        ("legacy", "views", "count"),
        ("ext_views", "count"),
        ("legacy", "ext_views", "count"),
    ]
    for p in paths:
        node = res
        try:
            for k in p:
                node = node[k]
            if node is None:
                continue
            # ép kiểu an toàn
            if isinstance(node, (int, float)):
                return int(node)
            if isinstance(node, str) and node.isdigit():
                return int(node)
        except Exception:
            continue
    return None


def _extract_tweet_item(item_content: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a single tweet/reply structure (kèm view_count)."""
    try:
        res = item_content.get("tweet_results", {}).get("result", {})
        if not res or res.get("__typename") == "TweetTombstone":
            return {}

        legacy = res.get("legacy", {})
        user = res.get("core", {}).get("user_results", {}).get("result", {})
        user_legacy = user.get("legacy", {})

        view_count = _extract_view_count(res)

        return {
            # replies dùng reply_id; tweet gốc ta sẽ bỏ nó đi ở trên
            "reply_id": res.get("rest_id"),
            # với replies, conversation_id_str là id của tweet gốc
            "post_id": legacy.get("conversation_id_str") or res.get("rest_id"),

            "created_at": legacy.get("created_at"),
            "text": legacy.get("full_text"),

            "user_id": user.get("rest_id"),
            "username": user.get("core", {}).get("screen_name"),
            "displayname": user.get("core", {}).get("name"),
            "verified_flag": user.get("is_blue_verified"),

            "like_count": legacy.get("favorite_count"),
            "reply_count": legacy.get("reply_count"),
            "retweet_count": legacy.get("retweet_count"),
            "quote_count": legacy.get("quote_count"),

            # —— user stats ——
            "followers_count": user_legacy.get("followers_count"),
            "friends_count": user_legacy.get("friends_count"),
            "favourites_count": user_legacy.get("favourites_count"),
            "listed_count": user_legacy.get("listed_count"),
            "media_count": user_legacy.get("media_count"),

            # —— misc ——
            "view_count": view_count,
            "lang": legacy.get("lang"),
        }
    except Exception:
        return {}
