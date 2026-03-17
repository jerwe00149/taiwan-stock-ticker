"""股票 API"""

from fastapi import APIRouter, Query
from backend.database import get_conn
from backend.twse.client import TOP_STOCKS

router = APIRouter(tags=["stocks"])


@router.get("/stocks")
def list_stocks():
    """列出所有追蹤的股票"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tickers ORDER BY symbol").fetchall()
    conn.close()
    
    if rows:
        return [dict(r) for r in rows]
    
    # 回傳預設清單
    return [
        {"symbol": sym, "name": info[0], "sector": info[1], "market": info[2]}
        for sym, info in sorted(TOP_STOCKS.items())
    ]


@router.get("/stocks/search")
def search_stocks(q: str = Query(..., min_length=1)):
    """搜尋股票（代號或名稱）"""
    results = []
    q_lower = q.lower()
    for sym, (name, sector, market) in TOP_STOCKS.items():
        if q_lower in sym or q_lower in name.lower():
            results.append({
                "symbol": sym, "name": name,
                "sector": sector, "market": market,
            })
    return results[:10]


@router.get("/stocks/{symbol}/ohlc")
def get_ohlc(
    symbol: str,
    start: str = Query(None, description="YYYY-MM-DD"),
    end: str = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(120, ge=1, le=500),
):
    """取得個股日K線"""
    conn = get_conn()
    
    query = "SELECT * FROM ohlc WHERE symbol = ?"
    params = [symbol]
    
    if start:
        query += " AND date >= ?"
        params.append(start)
    if end:
        query += " AND date <= ?"
        params.append(end)
    
    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(r) for r in reversed(rows)]
