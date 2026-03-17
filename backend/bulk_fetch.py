"""批次抓取台股資料 + 新聞

Usage:
    python -m backend.bulk_fetch              # 抓取 TOP 25 股票，近3個月
    python -m backend.bulk_fetch --symbol 2330 --months 12
"""

import argparse
import logging
from datetime import datetime, timedelta

from backend.database import get_conn, init_db
from backend.twse.client import TOP_STOCKS, fetch_ohlc
from backend.twse.news import fetch_all_news
from backend.pipeline.layer0 import filter_article

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def bulk_fetch_ohlc(symbols: list, months: int = 3):
    """批次抓取 K 線資料"""
    conn = get_conn()
    end = datetime.now()
    start = end - timedelta(days=months * 30)
    
    for sym in symbols:
        info = TOP_STOCKS.get(sym, ("未知", "未知", "TWSE"))
        logger.info(f"抓取 {sym} ({info[0]}) K線...")
        
        data = fetch_ohlc(sym, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        
        for row in data:
            conn.execute(
                """INSERT OR REPLACE INTO ohlc 
                   (symbol, date, open, high, low, close, volume, turnover, transactions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sym, row["date"], row["open"], row["high"], row["low"],
                 row["close"], row["volume"], row["turnover"], row["transactions"]),
            )
        
        # 更新 tickers 表
        conn.execute(
            """INSERT OR REPLACE INTO tickers (symbol, name, market, sector, last_ohlc_fetch)
               VALUES (?, ?, ?, ?, ?)""",
            (sym, info[0], info[2], info[1], datetime.now().isoformat()),
        )
        
        conn.commit()
        logger.info(f"  → {len(data)} 筆 K 線")
    
    conn.close()


def bulk_fetch_news(symbols: list):
    """批次抓取新聞"""
    conn = get_conn()
    
    for sym in symbols:
        info = TOP_STOCKS.get(sym, ("未知", "未知", "TWSE"))
        logger.info(f"抓取 {sym} ({info[0]}) 新聞...")
        
        articles = fetch_all_news(sym)
        passed = 0
        
        for art in articles:
            # Layer 0 過濾
            ok, reason = filter_article(art["title"], art.get("description", ""), sym)
            
            conn.execute(
                """INSERT OR IGNORE INTO news_raw 
                   (id, title, description, publisher, author, published_at, article_url, tickers_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (art["id"], art["title"], art["description"], art["publisher"],
                 art["author"], art["published_at"], art["article_url"], art["tickers_json"]),
            )
            
            conn.execute(
                "INSERT OR IGNORE INTO news_ticker (news_id, symbol) VALUES (?, ?)",
                (art["id"], sym),
            )
            
            conn.execute(
                """INSERT OR REPLACE INTO layer0_results (news_id, symbol, passed, reason)
                   VALUES (?, ?, ?, ?)""",
                (art["id"], sym, int(ok), reason),
            )
            
            if ok:
                passed += 1
        
        conn.execute(
            "UPDATE tickers SET last_news_fetch = ? WHERE symbol = ?",
            (datetime.now().isoformat(), sym),
        )
        
        conn.commit()
        logger.info(f"  → {len(articles)} 篇新聞, {passed} 篇通過 Layer 0")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="批次抓取台股資料")
    parser.add_argument("--symbol", type=str, help="指定股票代號")
    parser.add_argument("--months", type=int, default=3, help="抓取幾個月 (default: 3)")
    parser.add_argument("--news-only", action="store_true", help="只抓新聞")
    parser.add_argument("--ohlc-only", action="store_true", help="只抓K線")
    args = parser.parse_args()
    
    init_db()
    
    symbols = [args.symbol] if args.symbol else list(TOP_STOCKS.keys())
    
    if not args.news_only:
        bulk_fetch_ohlc(symbols, args.months)
    
    if not args.ohlc_only:
        bulk_fetch_news(symbols)
    
    logger.info("完成！")


if __name__ == "__main__":
    main()
