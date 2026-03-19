"""每日自動更新台股資料（K線 + 新聞）"""
import warnings; warnings.filterwarnings('ignore')
from backend.database import get_conn
from backend.twse.client import fetch_twse_ohlc, TOP_STOCKS
from backend.twse.news import fetch_all_news
from datetime import datetime
import time

def update():
    conn = get_conn()
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=10000')
    
    today = datetime.now()
    date_str = f"{today.year}{today.month:02d}01"
    
    print(f"📈 更新 K 線 — {today.strftime('%Y-%m-%d')}")
    for sym, (name, sector, market) in TOP_STOCKS.items():
        try:
            if market == "TPEx":
                continue  # TPEx uses different API
            data = fetch_twse_ohlc(sym, date_str)
            for row in data:
                conn.execute('INSERT OR REPLACE INTO ohlc VALUES (?,?,?,?,?,?,?,?,?)',
                    (sym, row['date'], row['open'], row['high'], row['low'], row['close'], row['volume'], row['turnover'], row['transactions']))
            print(f"  {sym} {name}: {len(data)} 筆")
        except Exception as e:
            print(f"  {sym} {name}: 失敗 {e}")
        time.sleep(3)
    conn.commit()
    
    print(f"\n📰 更新新聞")
    total = 0
    for sym, (name, sector, market) in TOP_STOCKS.items():
        try:
            news = fetch_all_news(sym)
            added = 0
            for a in news:
                conn.execute('INSERT OR IGNORE INTO news_raw (source,source_id,title,description,url,published_at) VALUES (?,?,?,?,?,?)',
                    (a['source'], a['source_id'], a['title'], a.get('description',''), a['url'], a['published_at']))
                rid = conn.execute('SELECT id FROM news_raw WHERE source=? AND source_id=?', (a['source'], a['source_id'])).fetchone()
                if rid:
                    conn.execute('INSERT OR IGNORE INTO news_ticker (news_id, symbol) VALUES (?,?)', (rid[0], sym))
                    added += 1
            total += added
            if added: print(f"  {sym} {name}: +{added} 篇")
        except: pass
        time.sleep(1)
    conn.commit()
    conn.close()
    print(f"\n✅ 完成！新增 {total} 篇新聞")

if __name__ == "__main__":
    update()
