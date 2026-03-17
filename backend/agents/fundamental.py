"""🕵️ Agent 1: 基本面分析師 (Fundamental Analyst)

評估資產內在價值與宏觀經濟影響。
"""

import logging
from typing import Dict, Any
from backend.database import get_conn

logger = logging.getLogger(__name__)


def analyze(symbol: str, ohlc_data: list, news_data: list, company_info: dict) -> Dict[str, Any]:
    """基本面分析
    
    Returns:
        {
            "conclusion": "bullish/bearish/neutral",
            "valuation": "undervalued/overvalued/fair",
            "key_metrics": {...},
            "reasoning": "...",
            "confidence": 0-100
        }
    """
    name = company_info.get("name", symbol)
    sector = company_info.get("sector", "未知")
    
    # 計算基本技術指標作為價值參考
    if not ohlc_data:
        return {
            "conclusion": "neutral",
            "valuation": "unknown",
            "key_metrics": {},
            "reasoning": f"缺少 {name} 的歷史數據，無法進行基本面分析。",
            "confidence": 10
        }
    
    prices = [d["close"] for d in ohlc_data if d.get("close")]
    volumes = [d["volume"] for d in ohlc_data if d.get("volume")]
    
    current_price = prices[-1] if prices else 0
    
    # 計算移動平均
    ma20 = sum(prices[-20:]) / min(20, len(prices)) if prices else 0
    ma60 = sum(prices[-60:]) / min(60, len(prices)) if len(prices) >= 10 else ma20
    ma120 = sum(prices[-120:]) / min(120, len(prices)) if len(prices) >= 30 else ma60
    
    # 價格相對於長期均線的位置
    price_vs_ma120 = ((current_price - ma120) / ma120 * 100) if ma120 else 0
    
    # 成交量趨勢
    recent_vol = sum(volumes[-5:]) / min(5, len(volumes)) if volumes else 0
    avg_vol = sum(volumes[-60:]) / min(60, len(volumes)) if volumes else 0
    vol_ratio = recent_vol / avg_vol if avg_vol else 1
    
    # 新聞情緒統計
    positive_news = sum(1 for n in news_data if n.get("sentiment") == "positive")
    negative_news = sum(1 for n in news_data if n.get("sentiment") == "negative")
    total_news = len(news_data)
    
    # 判斷估值
    if price_vs_ma120 > 20:
        valuation = "overvalued"
        val_desc = f"股價高於120日均線 {price_vs_ma120:.1f}%，可能偏高估"
    elif price_vs_ma120 < -15:
        valuation = "undervalued"
        val_desc = f"股價低於120日均線 {abs(price_vs_ma120):.1f}%，可能偏低估"
    else:
        valuation = "fair"
        val_desc = f"股價接近120日均線（偏差 {price_vs_ma120:+.1f}%），估值合理"
    
    # 綜合判斷
    bullish_signals = 0
    bearish_signals = 0
    
    if current_price > ma20: bullish_signals += 1
    else: bearish_signals += 1
    
    if current_price > ma60: bullish_signals += 1
    else: bearish_signals += 1
    
    if vol_ratio > 1.2: bullish_signals += 1
    elif vol_ratio < 0.7: bearish_signals += 1
    
    if positive_news > negative_news: bullish_signals += 1
    elif negative_news > positive_news: bearish_signals += 1
    
    if bullish_signals > bearish_signals:
        conclusion = "bullish"
    elif bearish_signals > bullish_signals:
        conclusion = "bearish"
    else:
        conclusion = "neutral"
    
    confidence = min(90, 40 + abs(bullish_signals - bearish_signals) * 15)
    
    reasoning = (
        f"【{name}（{symbol}）基本面分析】\n"
        f"▸ 產業：{sector}\n"
        f"▸ 現價：{current_price:.1f}\n"
        f"▸ 估值：{val_desc}\n"
        f"▸ 均線排列：MA20={ma20:.1f} / MA60={ma60:.1f} / MA120={ma120:.1f}\n"
        f"▸ 量能：近5日均量為60日均量的 {vol_ratio:.1f}x\n"
        f"▸ 新聞面：正面{positive_news}篇 / 負面{negative_news}篇 / 共{total_news}篇\n"
        f"▸ 結論：基本面呈現{'多頭' if conclusion == 'bullish' else '空頭' if conclusion == 'bearish' else '中性'}格局"
    )
    
    return {
        "conclusion": conclusion,
        "valuation": valuation,
        "key_metrics": {
            "current_price": current_price,
            "ma20": round(ma20, 1),
            "ma60": round(ma60, 1),
            "ma120": round(ma120, 1),
            "price_vs_ma120_pct": round(price_vs_ma120, 1),
            "volume_ratio": round(vol_ratio, 2),
            "positive_news": positive_news,
            "negative_news": negative_news,
        },
        "reasoning": reasoning,
        "confidence": confidence,
    }
