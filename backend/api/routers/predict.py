"""預測 API"""

from fastapi import APIRouter
from backend.database import get_conn

router = APIRouter(tags=["predict"])


@router.get("/predict/{symbol}/forecast")
def get_forecast(symbol: str):
    """取得 AI 預測"""
    conn = get_conn()
    
    rows = conn.execute(
        """SELECT * FROM predictions 
           WHERE symbol = ? 
           ORDER BY date DESC, horizon
           LIMIT 10""",
        [symbol],
    ).fetchall()
    conn.close()
    
    return [dict(r) for r in rows]
