"""多代理分析 API"""

from fastapi import APIRouter, Query
from backend.database import get_conn
from backend.twse.client import TOP_STOCKS
from backend.agents.lead_trader import synthesize

router = APIRouter(tags=["analysis"])


@router.get("/analysis/{symbol}")
def run_analysis(symbol: str, days: int = Query(120, ge=10, le=500)):
    """執行多代理市場分析
    
    Returns 5-agent structured analysis + trade decision
    """
    conn = get_conn()
    
    # 取得 OHLC 數據
    ohlc = conn.execute(
        "SELECT * FROM ohlc WHERE symbol = ? ORDER BY date DESC LIMIT ?",
        [symbol, days],
    ).fetchall()
    ohlc = [dict(r) for r in reversed(ohlc)]
    
    # 取得新聞
    news = conn.execute(
        """SELECT n.*, l.sentiment, l.sentiment_score, l.summary
           FROM news_raw n
           JOIN news_ticker nt ON n.id = nt.news_id
           LEFT JOIN layer1_results l ON n.id = l.news_id AND l.symbol = nt.symbol
           WHERE nt.symbol = ? ORDER BY n.published_at DESC LIMIT 50""",
        [symbol],
    ).fetchall()
    news = [dict(r) for r in news]
    
    conn.close()
    
    # 公司資訊
    info = TOP_STOCKS.get(symbol, ("未知", "未知", "TWSE"))
    company_info = {"name": info[0], "sector": info[1], "market": info[2]}
    
    # 執行分析
    result = synthesize(symbol, ohlc, news, company_info)
    
    # 移除 raw_reports (太大)
    result.pop("raw_reports", None)
    
    return result
