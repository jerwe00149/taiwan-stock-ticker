"""歷史新聞抓取（分頁搜尋）"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import List, Dict

import requests

logger = logging.getLogger(__name__)


def fetch_cnyes_historical(symbol: str, company_name: str, max_pages: int = 10) -> List[Dict]:
    """從 CNYES 搜尋 API 分頁抓取歷史新聞"""
    all_results = []
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    for page in range(1, max_pages + 1):
        url = "https://api.cnyes.com/media/api/v1/search"
        params = {"q": company_name, "limit": 30, "page": page}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"Page {page} failed for {company_name}: {e}")
            break
        
        items_container = data.get("items", {})
        if isinstance(items_container, dict):
            items = items_container.get("data", [])
        elif isinstance(items_container, list):
            items = items_container
        else:
            items = []
        
        if not items:
            break
        
        for item in items:
            title = item.get("title", "").replace("<mark>", "").replace("</mark>", "")
            content = item.get("summary", "") or item.get("content", "")
            if isinstance(content, str):
                content = content.replace("<mark>", "").replace("</mark>", "")
            
            news_id = hashlib.md5(
                f"cnyes_{item.get('newsId', '')}".encode()
            ).hexdigest()[:16]
            
            pub_ts = item.get("publishAt") or item.get("created_at") or 0
            pub_str = ""
            if pub_ts:
                pub_str = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%dT%H:%M:%S")
            
            all_results.append({
                "id": news_id,
                "title": title,
                "description": content[:500] if content else "",
                "publisher": "鉅亨網",
                "author": item.get("author", ""),
                "published_at": pub_str,
                "article_url": f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                "tickers_json": json.dumps([symbol]),
            })
        
        logger.info(f"  {company_name} page {page}: {len(items)} articles")
        time.sleep(2)
    
    # Deduplicate by title prefix
    seen = set()
    unique = []
    for n in all_results:
        key = n["title"][:25]
        if key not in seen:
            seen.add(key)
            unique.append(n)
    
    return unique
