"""📈 Agent 2: 技術面分析師 (Technical Analyst)

分析價格趨勢與動能，尋找最佳進出場時機。
RSI / MACD / Bollinger Bands / 量價關係
"""

import math
from typing import Dict, Any, List


def _calc_rsi(prices: List[float], period: int = 14) -> float:
    """計算 RSI"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    recent = deltas[-(period):]
    
    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]
    
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0.001
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _calc_macd(prices: List[float]) -> Dict[str, float]:
    """計算 MACD (12, 26, 9)"""
    def ema(data, period):
        if len(data) < period:
            return data[-1] if data else 0
        k = 2 / (period + 1)
        val = sum(data[:period]) / period
        for p in data[period:]:
            val = p * k + val * (1 - k)
        return val
    
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    macd_line = ema12 - ema26
    
    # Signal line (simplified)
    if len(prices) >= 35:
        macd_values = []
        for i in range(26, len(prices)):
            e12 = ema(prices[:i+1], 12)
            e26 = ema(prices[:i+1], 26)
            macd_values.append(e12 - e26)
        signal = ema(macd_values, 9) if len(macd_values) >= 9 else macd_line
    else:
        signal = macd_line
    
    histogram = macd_line - signal
    
    return {"macd": macd_line, "signal": signal, "histogram": histogram}


def _calc_bollinger(prices: List[float], period: int = 20) -> Dict[str, float]:
    """計算布林通道"""
    if len(prices) < period:
        return {"upper": 0, "middle": 0, "lower": 0, "bandwidth": 0}
    
    recent = prices[-period:]
    middle = sum(recent) / period
    std = math.sqrt(sum((p - middle) ** 2 for p in recent) / period)
    
    upper = middle + 2 * std
    lower = middle - 2 * std
    bandwidth = (upper - lower) / middle * 100 if middle else 0
    
    return {
        "upper": round(upper, 1),
        "middle": round(middle, 1),
        "lower": round(lower, 1),
        "bandwidth": round(bandwidth, 2),
    }


def analyze(symbol: str, ohlc_data: list, company_info: dict) -> Dict[str, Any]:
    """技術面分析"""
    name = company_info.get("name", symbol)
    
    if len(ohlc_data) < 5:
        return {
            "conclusion": "neutral",
            "trend": "unknown",
            "support_resistance": {},
            "indicators": {},
            "reasoning": f"數據不足，無法進行技術分析。",
            "confidence": 10,
        }
    
    prices = [d["close"] for d in ohlc_data]
    highs = [d["high"] for d in ohlc_data]
    lows = [d["low"] for d in ohlc_data]
    volumes = [d["volume"] for d in ohlc_data]
    current = prices[-1]
    
    # RSI
    rsi = _calc_rsi(prices)
    
    # MACD
    macd = _calc_macd(prices)
    
    # Bollinger Bands
    bb = _calc_bollinger(prices)
    
    # 支撐壓力
    recent_lows = sorted(lows[-20:])
    recent_highs = sorted(highs[-20:], reverse=True)
    support = recent_lows[1] if len(recent_lows) > 1 else recent_lows[0]
    resistance = recent_highs[1] if len(recent_highs) > 1 else recent_highs[0]
    
    # 量價分析
    recent_vol = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1]
    prev_vol = sum(volumes[-20:-5]) / 15 if len(volumes) >= 20 else recent_vol
    vol_trend = "放量" if recent_vol > prev_vol * 1.3 else "縮量" if recent_vol < prev_vol * 0.7 else "量能持平"
    
    price_change_5d = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) >= 6 else 0
    
    # 綜合判斷
    bullish = 0
    bearish = 0
    signals = []
    
    # RSI
    if rsi > 70:
        bearish += 1
        signals.append(f"RSI={rsi:.1f} 超買區")
    elif rsi < 30:
        bullish += 1
        signals.append(f"RSI={rsi:.1f} 超賣區")
    else:
        signals.append(f"RSI={rsi:.1f} 中性")
    
    # MACD
    if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
        bullish += 1
        signals.append("MACD 多頭排列（柱狀體為正）")
    elif macd["histogram"] < 0:
        bearish += 1
        signals.append("MACD 空頭排列（柱狀體為負）")
    
    # Bollinger
    if current > bb["upper"]:
        bearish += 1
        signals.append(f"股價突破布林上軌 {bb['upper']}")
    elif current < bb["lower"]:
        bullish += 1
        signals.append(f"股價跌破布林下軌 {bb['lower']}")
    else:
        signals.append(f"股價在布林通道內（{bb['lower']}~{bb['upper']}）")
    
    # 量價配合
    if price_change_5d > 0 and vol_trend == "放量":
        bullish += 1
        signals.append("價漲量增，多頭確認")
    elif price_change_5d < 0 and vol_trend == "放量":
        bearish += 1
        signals.append("價跌量增，空頭確認")
    elif price_change_5d > 0 and vol_trend == "縮量":
        signals.append("價漲量縮，多頭動能不足")
    
    if bullish > bearish:
        conclusion = "bullish"
        trend = "多頭趨勢"
    elif bearish > bullish:
        conclusion = "bearish"
        trend = "空頭趨勢"
    else:
        conclusion = "neutral"
        trend = "盤整格局"
    
    confidence = min(90, 35 + abs(bullish - bearish) * 15 + len(ohlc_data) // 10)
    
    reasoning = (
        f"【{name}（{symbol}）技術面分析】\n"
        f"▸ 趨勢判斷：{trend}\n"
        f"▸ 支撐：{support:.1f} / 壓力：{resistance:.1f}\n"
        f"▸ 技術訊號：\n  " + "\n  ".join(f"• {s}" for s in signals) + "\n"
        f"▸ 5日漲跌：{price_change_5d:+.2f}%，{vol_trend}\n"
        f"▸ 布林帶寬：{bb['bandwidth']:.1f}%（{'波動收斂' if bb['bandwidth'] < 5 else '波動擴大' if bb['bandwidth'] > 15 else '波動正常'}）"
    )
    
    return {
        "conclusion": conclusion,
        "trend": trend,
        "support_resistance": {
            "support": round(support, 1),
            "resistance": round(resistance, 1),
        },
        "indicators": {
            "rsi": round(rsi, 1),
            "macd": round(macd["macd"], 2),
            "macd_signal": round(macd["signal"], 2),
            "macd_histogram": round(macd["histogram"], 2),
            "bollinger_upper": bb["upper"],
            "bollinger_lower": bb["lower"],
            "bollinger_bandwidth": bb["bandwidth"],
            "volume_trend": vol_trend,
            "price_change_5d": round(price_change_5d, 2),
        },
        "signals": signals,
        "reasoning": reasoning,
        "confidence": confidence,
    }
