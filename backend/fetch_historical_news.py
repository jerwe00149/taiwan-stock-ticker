"""批次抓取 5 年歷史新聞

Usage:
    python -m backend.fetch_historical_news                    # 所有追蹤股票, 5年
    python -m backend.fetch_historical_news --symbol 2330      # 單一股票
    python -m backend.fetch_historical_news --years 2          # 2年
"""

import argparse
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from calendar import monthrange

import requests

from backend.database import get_conn, init_db
from backend.pipeline.layer0 import filter_article
from backend.twse.client import TOP_STOCKS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def fetch_month_news(year: int, month: int, max_pages: int = 5) -> list:
    """抓取指定月份的台股新聞"""
    start_ts = int(datetime(year, month, 1).timestamp())
    _, last_day = monthrange(year, month)
    end_ts = int(datetime(year, month, last_day, 23, 59, 59).timestamp())
    
    all_items = []
    for page in range(1, max_pages + 1):
        url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"
        params = {
            "limit": 30,
            "page": page,
            "startAt": start_ts,
            "endAt": end_ts,
        }
        
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"  {year}-{month:02d} page {page} failed: {e}")
            break
        
        items = data.get("items", {}).get("data", [])
        if not items:
            break
        
        all_items.extend(items)
        time.sleep(1.5)
    
    return all_items


def match_stock(item: dict, symbols_names: dict) -> list:
    """判斷新聞與哪些股票相關"""
    title = item.get("title", "")
    content = item.get("summary", "") or item.get("content", "") or ""
    text = f"{title} {content}"
    
    matched = []
    for sym, name in symbols_names.items():
        if sym in text or name in text:
            matched.append(sym)
    
    return matched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--pages-per-month", type=int, default=3)
    args = parser.parse_args()
    
    init_db()
    conn = get_conn()
    
    if args.symbol:
        info = TOP_STOCKS.get(args.symbol, ("未知", "未知", "TWSE"))
        symbols_names = {args.symbol: info[0]}
    else:
        symbols_names = {sym: info[0] for sym, info in TOP_STOCKS.items()}
    
    now = datetime.now()
    start_year = now.year - args.years
    total_news = 0
    total_matched = 0
    
    for year in range(start_year, now.year + 1):
        for month in range(1, 13):
            if year == start_year and month < now.month:
                continue
            if year == now.year and month > now.month:
                break
            
            logger.info(f"抓取 {year}-{month:02d} 新聞...")
            items = fetch_month_news(year, month, max_pages=args.pages_per_month)
            
            month_matched = 0
            for item in items:
                title = item.get("title", "").replace("<mark>", "").replace("</mark>", "")
                content = (item.get("summary", "") or item.get("content", "") or "")
                if isinstance(content, str):
                    content = content.replace("<mark>", "").replace("</mark>", "")
                
                matched_syms = match_stock(item, symbols_names)
                if not matched_syms:
                    continue
                
                news_id = hashlib.md5(
                    f"cnyes_{item.get('newsId', '')}".encode()
                ).hexdigest()[:16]
                
                pub_ts = item.get("publishAt") or item.get("created_at") or 0
                pub_str = datetime.fromtimestamp(pub_ts).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ) if pub_ts else ""
                
                conn.execute(
                    """INSERT OR IGNORE INTO news_raw 
                       (id, title, description, publisher, author, published_at, article_url, tickers_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (news_id, title, content[:500], "鉅亨網",
                     item.get("author", ""), pub_str,
                     f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                     json.dumps(matched_syms)),
                )
                
                for sym in matched_syms:
                    conn.execute(
                        "INSERT OR IGNORE INTO news_ticker (news_id, symbol) VALUES (?, ?)",
                        (news_id, sym),
                    )
                    ok, reason = filter_article(title, content, sym)
                    conn.execute(
                        "INSERT OR REPLACE INTO layer0_results (news_id, symbol, passed, reason) VALUES (?, ?, ?, ?)",
                        (news_id, sym, int(ok), reason),
                    )
                
                month_matched += 1
            
            conn.commit()
            total_news += len(items)
            total_matched += month_matched
            logger.info(f"  → {len(items)} 篇, {month_matched} 篇與追蹤股票相關")
            time.sleep(2)
    
    conn.close()
    logger.info(f"完成! 總共 {total_news} 篇新聞, {total_matched} 篇與追蹤股票相關")


if __name__ == "__main__":
    main()
