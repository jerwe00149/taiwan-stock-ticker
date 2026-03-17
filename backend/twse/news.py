"""台股新聞來源

主要來源:
1. 鉅亨網 (CNYES) API — 結構化 JSON，最穩定
2. Yahoo 奇摩股市 RSS
3. MoneyDJ 理財網
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def fetch_cnyes_news(symbol: str, page: int = 1, limit: int = 30) -> List[Dict]:
    """從鉅亨網抓取個股新聞
    
    使用 api.cnyes.com 免費 API。
    """
    # 先抓台股新聞列表，再過濾相關個股
    url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"
    params = {
        "page": page,
        "limit": limit,
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"CNYES fetch failed: {e}")
        return []
    
    items_container = data.get("items", {})
    if isinstance(items_container, dict):
        items = items_container.get("data", [])
    elif isinstance(items_container, list):
        items = items_container
    else:
        items = []
    results = []
    
    for item in items:
        title = item.get("title", "")
        content = item.get("summary", "") or item.get("content", "")
        
        # 檢查新聞是否提到目標股票
        if symbol not in title and symbol not in content:
            # 也檢查公司名稱
            from backend.twse.client import TOP_STOCKS
            stock_info = TOP_STOCKS.get(symbol)
            if stock_info and stock_info[0] not in title and stock_info[0] not in content:
                continue
        
        news_id = hashlib.md5(f"cnyes_{item.get('newsId', '')}".encode()).hexdigest()[:16]
        
        results.append({
            "id": news_id,
            "title": title,
            "description": content[:500],
            "publisher": "鉅亨網",
            "author": item.get("author", ""),
            "published_at": datetime.fromtimestamp(
                item.get("publishAt", 0) or item.get("created_at", 0) or 0
            ).strftime("%Y-%m-%dT%H:%M:%S") if (item.get("publishAt") or item.get("created_at")) else "",
            "article_url": f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
            "tickers_json": json.dumps([symbol]),
        })
    
    return results


def fetch_yahoo_tw_news(symbol: str) -> List[Dict]:
    """從 Yahoo 奇摩股市抓取個股新聞"""
    url = f"https://tw.stock.yahoo.com/quote/{symbol}.TW/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Yahoo TW fetch failed for {symbol}: {e}")
        return []
    
    # 簡易 HTML 解析（不依賴 BeautifulSoup）
    import re
    results = []
    
    # 找到 JSON-LD 或 script 中的新聞資料
    pattern = r'"title":"([^"]+)".*?"datePublished":"([^"]+)".*?"url":"([^"]+)"'
    matches = re.findall(pattern, resp.text)
    
    for title, pub_date, url in matches[:20]:
        news_id = hashlib.md5(f"yahoo_{url}".encode()).hexdigest()[:16]
        results.append({
            "id": news_id,
            "title": title,
            "description": "",
            "publisher": "Yahoo奇摩",
            "author": "",
            "published_at": pub_date,
            "article_url": url,
            "tickers_json": json.dumps([symbol]),
        })
    
    return results




def fetch_cnyes_search(symbol: str, limit: int = 30) -> List[Dict]:
    """用 CNYES 搜尋 API 抓取個股相關新聞"""
    from backend.twse.client import TOP_STOCKS
    info = TOP_STOCKS.get(symbol)
    query = info[0] if info else symbol  # 用公司名稱搜尋
    
    url = "https://api.cnyes.com/media/api/v1/search"
    params = {"q": query, "limit": limit}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"CNYES search failed for {query}: {e}")
        return []
    
    items_container = data.get("items", {})
    if isinstance(items_container, dict):
        items = items_container.get("data", [])
    elif isinstance(items_container, list):
        items = items_container
    else:
        items = []
    
    results = []
    for item in items:
        title = item.get("title", "").replace("<mark>", "").replace("</mark>", "")
        content = item.get("summary", "") or item.get("content", "")
        if isinstance(content, str):
            content = content.replace("<mark>", "").replace("</mark>", "")
        
        news_id = hashlib.md5(f"cnyes_s_{item.get('newsId', '')}".encode()).hexdigest()[:16]
        
        pub_ts = item.get("publishAt") or item.get("created_at") or 0
        pub_str = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%dT%H:%M:%S") if pub_ts else ""
        
        results.append({
            "id": news_id,
            "title": title,
            "description": content[:500] if content else "",
            "publisher": "鉅亨網",
            "author": item.get("author", ""),
            "published_at": pub_str,
            "article_url": f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
            "tickers_json": json.dumps([symbol]),
        })
    
    return results


def fetch_all_news(symbol: str) -> List[Dict]:
    """從所有來源抓取新聞，去重"""
    all_news = []
    
    # 鉅亨網（分類 + 搜尋）
    cnyes = fetch_cnyes_news(symbol)
    all_news.extend(cnyes)
    time.sleep(1)
    
    cnyes_search = fetch_cnyes_search(symbol)
    all_news.extend(cnyes_search)
    time.sleep(1)
    
    # Yahoo 奇摩
    yahoo = fetch_yahoo_tw_news(symbol)
    all_news.extend(yahoo)
    
    # 去重（by title similarity）
    seen_titles = set()
    unique = []
    for n in all_news:
        title_key = n["title"][:20]  # 前20字作為去重key
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(n)
    
    logger.info(f"Fetched {len(unique)} unique news for {symbol} "
                f"(cnyes={len(cnyes)}, yahoo={len(yahoo)})")
    return unique
