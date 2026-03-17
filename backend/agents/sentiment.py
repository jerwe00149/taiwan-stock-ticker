"""🔥 Agent 4: 市場情緒分析師 (Market Sentiment Analyst)

捕捉市場群體心理，判斷貪婪/恐懼程度。
"""

from typing import Dict, Any, List
import math


def _calc_fear_greed_index(ohlc_data: list, news_data: list) -> int:
    """計算恐懼貪婪指數 (0=極度恐懼, 100=極度貪婪)
    
    參考5個面向:
    1. 股價動能 (Price Momentum)
    2. 波動率 (Volatility)  
    3. 成交量 (Volume)
    4. 新聞情緒 (News Sentiment)
    5. 均線乖離 (Moving Average Deviation)
    """
    scores = []
    
    if len(ohlc_data) < 20:
        return 50
    
    prices = [d["close"] for d in ohlc_data]
    volumes = [d["volume"] for d in ohlc_data]
    current = prices[-1]
    
    # 1. 價格動能 (近5日 vs 近20日)
    change_5d = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) >= 6 else 0
    momentum_score = min(100, max(0, 50 + change_5d * 10))
    scores.append(momentum_score)
    
    # 2. 波動率 (高波動 = 恐懼)
    recent_ranges = [(ohlc_data[i]["high"] - ohlc_data[i]["low"]) / ohlc_data[i]["close"] * 100 
                     for i in range(-10, 0)]
    avg_range = sum(recent_ranges) / len(recent_ranges)
    vol_score = max(0, min(100, 80 - avg_range * 20))  # 高波動 → 低分(恐懼)
    scores.append(vol_score)
    
    # 3. 成交量趨勢
    recent_vol = sum(volumes[-5:]) / 5
    avg_vol = sum(volumes[-20:]) / 20
    vol_ratio = recent_vol / avg_vol if avg_vol else 1
    
    # 量增價漲 = 貪婪, 量增價跌 = 恐懼
    if change_5d > 0 and vol_ratio > 1:
        vol_sentiment = min(100, 50 + vol_ratio * 20)
    elif change_5d < 0 and vol_ratio > 1:
        vol_sentiment = max(0, 50 - vol_ratio * 20)
    else:
        vol_sentiment = 50
    scores.append(vol_sentiment)
    
    # 4. 新聞情緒
    if news_data:
        pos = sum(1 for n in news_data if n.get("sentiment") == "positive")
        neg = sum(1 for n in news_data if n.get("sentiment") == "negative")
        total = max(1, pos + neg)
        news_score = (pos / total) * 100
    else:
        news_score = 50
    scores.append(news_score)
    
    # 5. 均線乖離
    ma20 = sum(prices[-20:]) / 20
    deviation = (current - ma20) / ma20 * 100
    ma_score = min(100, max(0, 50 + deviation * 5))
    scores.append(ma_score)
    
    # 加權平均
    weights = [0.25, 0.20, 0.15, 0.25, 0.15]
    weighted = sum(s * w for s, w in zip(scores, weights))
    
    return round(weighted)


def _detect_herding(ohlc_data: list) -> Dict:
    """檢測羊群效應"""
    if len(ohlc_data) < 10:
        return {"detected": False, "type": "none"}
    
    # 連續同方向 = 可能羊群效應
    recent = ohlc_data[-10:]
    up_days = sum(1 for d in recent if d["close"] > d["open"])
    down_days = 10 - up_days
    
    if up_days >= 8:
        return {
            "detected": True,
            "type": "bullish_herding",
            "description": f"近10個交易日有{up_days}天收紅，市場可能過度樂觀，情緒反轉風險升高",
            "reversal_risk": "high",
        }
    elif down_days >= 8:
        return {
            "detected": True,
            "type": "bearish_herding",
            "description": f"近10個交易日有{down_days}天收黑，市場可能過度悲觀，存在超跌反彈機會",
            "reversal_risk": "high",
        }
    elif up_days >= 7 or down_days >= 7:
        return {
            "detected": True,
            "type": "mild_herding",
            "description": "市場情緒趨於一致，但尚未達到極端",
            "reversal_risk": "medium",
        }
    
    return {"detected": False, "type": "none", "reversal_risk": "low"}


def analyze(symbol: str, ohlc_data: list, news_data: list, company_info: dict) -> Dict[str, Any]:
    """市場情緒分析"""
    name = company_info.get("name", symbol)
    
    if len(ohlc_data) < 10:
        return {
            "conclusion": "neutral",
            "fear_greed_score": 50,
            "herding": {"detected": False},
            "sentiment_price_divergence": False,
            "reasoning": "數據不足，無法進行情緒分析。",
            "confidence": 10,
        }
    
    # 恐懼貪婪指數
    fg_score = _calc_fear_greed_index(ohlc_data, news_data)
    
    # 羊群效應
    herding = _detect_herding(ohlc_data)
    
    # 情緒標籤
    if fg_score <= 20:
        sentiment_label = "極度恐懼"
        emoji = "😱"
    elif fg_score <= 35:
        sentiment_label = "恐懼"
        emoji = "😰"
    elif fg_score <= 45:
        sentiment_label = "偏空"
        emoji = "😟"
    elif fg_score <= 55:
        sentiment_label = "中性"
        emoji = "😐"
    elif fg_score <= 65:
        sentiment_label = "偏多"
        emoji = "🙂"
    elif fg_score <= 80:
        sentiment_label = "貪婪"
        emoji = "😀"
    else:
        sentiment_label = "極度貪婪"
        emoji = "🤑"
    
    # 情緒與價格背離檢測
    prices = [d["close"] for d in ohlc_data]
    price_trend = "up" if prices[-1] > prices[-6] else "down" if len(prices) >= 6 else "flat"
    
    divergence = False
    divergence_desc = ""
    if fg_score > 70 and price_trend == "down":
        divergence = True
        divergence_desc = "⚠️ 情緒貪婪但股價下跌 — 可能是多頭陷阱"
    elif fg_score < 30 and price_trend == "up":
        divergence = True
        divergence_desc = "⚠️ 情緒恐懼但股價上漲 — 可能是空頭陷阱（聰明錢進場）"
    
    # 結論
    if fg_score <= 25:
        conclusion = "extreme_fear"
    elif fg_score >= 75:
        conclusion = "extreme_greed"
    elif fg_score < 45:
        conclusion = "bearish"
    elif fg_score > 55:
        conclusion = "bullish"
    else:
        conclusion = "neutral"
    
    confidence = min(90, 40 + abs(fg_score - 50) // 2 + (15 if herding["detected"] else 0))
    
    reasoning = (
        f"【{name}（{symbol}）市場情緒分析】\n"
        f"\n▸ 恐懼貪婪指數：{fg_score}/100 {emoji} {sentiment_label}\n"
        f"\n▸ 羊群效應：{'⚠️ 偵測到！' if herding['detected'] else '未偵測到'}\n"
    )
    
    if herding["detected"]:
        reasoning += f"  {herding.get('description', '')}\n"
        reasoning += f"  情緒反轉風險：{herding.get('reversal_risk', 'unknown')}\n"
    
    if divergence:
        reasoning += f"\n▸ 情緒背離：{divergence_desc}\n"
    
    reasoning += (
        f"\n▸ 交易啟示：\n"
        f"  {'情緒極度恐慌時，若基本面未受損，為逆勢佈局良機' if fg_score < 25 else ''}"
        f"  {'情緒極度貪婪，應警惕獲利了結壓力，考慮減碼' if fg_score > 75 else ''}"
        f"  {'情緒中性，依技術面與籌碼面方向操作' if 35 <= fg_score <= 65 else ''}"
    )
    
    return {
        "conclusion": conclusion,
        "fear_greed_score": fg_score,
        "sentiment_label": sentiment_label,
        "herding": herding,
        "sentiment_price_divergence": divergence,
        "divergence_description": divergence_desc,
        "reasoning": reasoning,
        "confidence": confidence,
    }
