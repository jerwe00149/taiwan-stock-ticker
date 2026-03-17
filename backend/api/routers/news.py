"""新聞 API"""

from fastapi import APIRouter, Query
from backend.database import get_conn

router = APIRouter(tags=["news"])


@router.get("/news/{symbol}")
def get_news(
    symbol: str,
    date: str = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100),
):
    """取得個股新聞（含 AI 分析結果）"""
    conn = get_conn()
    
    query = """
        SELECT n.*, l.sentiment, l.sentiment_score, l.summary,
               l.reason_growth, l.reason_decrease, l.relevance,
               a.return_t1, a.return_t5
        FROM news_raw n
        JOIN news_ticker nt ON n.id = nt.news_id
        LEFT JOIN layer1_results l ON n.id = l.news_id AND l.symbol = nt.symbol
        LEFT JOIN news_aligned a ON n.id = a.news_id AND a.symbol = nt.symbol
        WHERE nt.symbol = ?
    """
    params = [symbol]
    
    if date:
        query += " AND date(n.published_at) = ?"
        params.append(date)
    
    query += " ORDER BY n.published_at DESC LIMIT ?"
    params.append(limit)
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(r) for r in rows]


@router.get("/news/{symbol}/timeline")
def get_news_timeline(symbol: str, start: str = None, end: str = None):
    """新聞時間軸（每日情緒分數）"""
    conn = get_conn()
    
    query = """
        SELECT date(n.published_at) as date,
               COUNT(*) as news_count,
               AVG(l.sentiment_score) as avg_sentiment,
               SUM(CASE WHEN l.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
               SUM(CASE WHEN l.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count
        FROM news_raw n
        JOIN news_ticker nt ON n.id = nt.news_id
        LEFT JOIN layer1_results l ON n.id = l.news_id AND l.symbol = nt.symbol
        WHERE nt.symbol = ?
    """
    params = [symbol]
    
    if start:
        query += " AND date(n.published_at) >= ?"
        params.append(start)
    if end:
        query += " AND date(n.published_at) <= ?"
        params.append(end)
    
    query += " GROUP BY date(n.published_at) ORDER BY date"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(r) for r in rows]
