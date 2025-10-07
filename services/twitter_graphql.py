import json, requests, time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import List, Dict, Any, Optional
from services.cookies_manager import CookiesManager, CookieAccount
from services.proxy_manager import ProxyManager


class RateLimitError(Exception): pass


# ------------------ BASE FUNCTIONS ------------------

def _headers_from_account(acc: CookieAccount, bearer: str) -> Dict[str, str]:
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in acc.cookies])
    ct0 = next((c["value"] for c in acc.cookies if c["name"] == "ct0"), "")
    return {
        "authorization": bearer,
        "cookie": cookie_str,
        "x-csrf-token": ct0,
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"
    }


@retry(
    retry=retry_if_exception_type((requests.exceptions.RequestException, RateLimitError)),
    wait=wait_exponential(multiplier=3, min=3, max=120),
    stop=stop_after_attempt(5),
    reraise=True
)
def _call_graphql(url: str, params: Dict[str, Any], headers: Dict[str, str], proxy: Optional[str] = None):
    proxies = {"http": proxy, "https": proxy} if proxy else None
    r = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=20)
    if r.status_code == 429:
        raise RateLimitError("Rate limit reached")
    if r.status_code in (401, 403):
        raise requests.exceptions.RequestException(f"auth: {r.status_code}")
    r.raise_for_status()
    return r.json()


# ------------------ MAIN FETCHERS ------------------

def fetch_tweet_detail(tweet_id: str, cookies_mgr: CookiesManager,
                       bearer: str, gql_key: str):
    """Fetch full detail for a single tweet."""
    url = f"https://x.com/i/api/graphql/{gql_key}/TweetResultByRestId"
    params = {"variables": json.dumps({"tweetId": tweet_id, "includePromotedContent": True})}
    acc = cookies_mgr.get_next()
    if not acc:
        raise Exception("no cookie account available")
    headers = _headers_from_account(acc, bearer)
    data = _call_graphql(url, params, headers)
    cookies_mgr.increment(acc, 1)
    return data


def fetch_replies(tweet_id: str, cookies_mgr: CookiesManager,
                  bearer: str, gql_key: str, limit: int = 100):
    """Fetch replies for a given tweet."""
    url = f"https://x.com/i/api/graphql/{gql_key}/TweetDetail"
    params = {"variables": json.dumps({"focalTweetId": tweet_id})}

    acc = cookies_mgr.get_next()
    if not acc:
        raise Exception("no cookie account available")
    headers = _headers_from_account(acc, bearer)
    resp = _call_graphql(url, params, headers)
    cookies_mgr.increment(acc, 1)

    replies = []
    insts = resp.get("data", {}).get("threaded_conversation_with_injections", {}).get("instructions", [])
    for inst in insts:
        entries = inst.get("entries") or []
        for entry in entries:
            content = entry.get("content", {}).get("itemContent", {})
            result = (content.get("tweet_results") or {}).get("result") or {}
            if not result:
                continue
            legacy = result.get("legacy", {})
            user_legacy = result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
            replies.append({
                "reply_id": result.get("rest_id"),
                "post_id": tweet_id,
                "created_at": legacy.get("created_at"),
                "text": legacy.get("full_text"),
                "user_id": result.get("core", {}).get("user_results", {}).get("result", {}).get("rest_id"),
                "username": user_legacy.get("screen_name"),
                "displayname": user_legacy.get("name"),
                "verified_flag": user_legacy.get("verified"),
                "like_count": legacy.get("favorite_count"),
                "reply_count": legacy.get("reply_count"),
                "retweet_count": legacy.get("retweet_count"),
            })
            if len(replies) >= limit:
                return replies
    return replies
