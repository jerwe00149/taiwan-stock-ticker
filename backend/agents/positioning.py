"""🎲 Agent 3: 籌碼與結構分析師 (Positioning & Structure Analyst)

使用 WHO-WHOM-WHAT 因果框架分析籌碼面。
分析三大法人買賣超、融資融券、大戶持股等。
"""

from typing import Dict, Any, List
import math


def _estimate_institutional_flow(ohlc_data: list) -> Dict:
    """從量價關係推估法人動向"""
    if len(ohlc_data) < 10:
        return {"direction": "neutral", "intensity": 0}
    
    # 大量+收紅 → 法人買進跡象
    # 大量+收黑 → 法人賣出跡象
    recent = ohlc_data[-10:]
    avg_vol = sum(d["volume"] for d in ohlc_data[-60:]) / min(60, len(ohlc_data))
    
    buy_pressure = 0
    sell_pressure = 0
    
    for d in recent:
        vol_ratio = d["volume"] / avg_vol if avg_vol else 1
        if d["close"] > d["open"]:  # 收紅
            buy_pressure += vol_ratio
        elif d["close"] < d["open"]:  # 收黑
            sell_pressure += vol_ratio
    
    net = buy_pressure - sell_pressure
    intensity = min(100, abs(net) * 10)
    
    return {
        "direction": "buying" if net > 1 else "selling" if net < -1 else "neutral",
        "intensity": round(intensity),
        "buy_pressure": round(buy_pressure, 1),
        "sell_pressure": round(sell_pressure, 1),
    }


def _estimate_gamma_exposure(ohlc_data: list) -> Dict:
    """從價格波動模式推估 Gamma 曝險
    
    負 Gamma = 造市商被迫追漲殺跌 → 波動放大
    正 Gamma = 造市商逆勢操作 → 波動收斂
    """
    if len(ohlc_data) < 20:
        return {"gamma_state": "unknown", "volatility_forecast": "unknown"}
    
    recent = ohlc_data[-20:]
    
    # 計算日內波動率
    intraday_ranges = [(d["high"] - d["low"]) / d["close"] * 100 for d in recent]
    avg_range = sum(intraday_ranges) / len(intraday_ranges)
    
    # 計算收盤到收盤波動
    close_changes = [abs(recent[i]["close"] - recent[i-1]["close"]) / recent[i-1]["close"] * 100 
                     for i in range(1, len(recent))]
    avg_change = sum(close_changes) / len(close_changes) if close_changes else 0
    
    # 波動加速 = 可能負 Gamma（追漲殺跌）
    early_ranges = intraday_ranges[:10]
    late_ranges = intraday_ranges[10:]
    vol_acceleration = (sum(late_ranges) / len(late_ranges)) / (sum(early_ranges) / len(early_ranges)) if early_ranges else 1
    
    if vol_acceleration > 1.3:
        gamma_state = "negative"
        vol_forecast = "amplified"
    elif vol_acceleration < 0.7:
        gamma_state = "positive"
        vol_forecast = "compressed"
    else:
        gamma_state = "neutral"
        vol_forecast = "stable"
    
    return {
        "gamma_state": gamma_state,
        "volatility_forecast": vol_forecast,
        "avg_daily_range_pct": round(avg_range, 2),
        "avg_daily_change_pct": round(avg_change, 2),
        "volatility_acceleration": round(vol_acceleration, 2),
    }


def _find_pinning_levels(ohlc_data: list) -> List[float]:
    """找出股價磁吸區（成交量最集中的價位）"""
    if len(ohlc_data) < 10:
        return []
    
    # 用成交量加權的價格分布
    price_volume = {}
    for d in ohlc_data[-60:]:
        # 將價格四捨五入到整數（台股常以整數價位為磁吸點）
        rounded = round(d["close"] / 5) * 5  # 以5元為單位
        price_volume[rounded] = price_volume.get(rounded, 0) + d["volume"]
    
    # 排序找出成交量最大的3個價位
    sorted_levels = sorted(price_volume.items(), key=lambda x: x[1], reverse=True)
    return [level for level, _ in sorted_levels[:3]]


def analyze(symbol: str, ohlc_data: list, company_info: dict) -> Dict[str, Any]:
    """籌碼面分析（WHO-WHOM-WHAT 框架）"""
    name = company_info.get("name", symbol)
    
    if len(ohlc_data) < 10:
        return {
            "conclusion": "neutral",
            "who_whom_what": {},
            "gamma": {},
            "pinning_levels": [],
            "reasoning": "數據不足，無法進行籌碼分析。",
            "confidence": 10,
        }
    
    # 分析
    flow = _estimate_institutional_flow(ohlc_data)
    gamma = _estimate_gamma_exposure(ohlc_data)
    pinning = _find_pinning_levels(ohlc_data)
    current_price = ohlc_data[-1]["close"]
    
    # WHO-WHOM-WHAT 框架
    if gamma["gamma_state"] == "negative":
        who = "持有負 Gamma 部位的造市商與選擇權賣方"
        whom = "趨勢追逐者、散戶投資人、槓桿ETF持有者"
        what = "被迫在下跌時賣出（Delta 避險），在上漲時買進，放大市場波動"
        framework_conclusion = "波動率將被放大"
    elif gamma["gamma_state"] == "positive":
        who = "持有正 Gamma 部位的造市商"
        whom = "試圖突破的投機者"
        what = "在上漲時賣出、下跌時買進，壓抑波動，股價傾向區間盤整"
        framework_conclusion = "波動率將被壓縮"
    else:
        who = "造市商與法人機構"
        whom = "市場參與者"
        what = "維持正常避險操作，無明顯方向性力量"
        framework_conclusion = "波動率維持正常"
    
    # 籌碼方向
    if flow["direction"] == "buying":
        chip_direction = "多頭"
        chip_desc = f"近10日量價分析顯示買盤壓力（{flow['buy_pressure']:.1f}）大於賣盤（{flow['sell_pressure']:.1f}），法人可能持續買進"
    elif flow["direction"] == "selling":
        chip_direction = "空頭"
        chip_desc = f"近10日量價分析顯示賣盤壓力（{flow['sell_pressure']:.1f}）大於買盤（{flow['buy_pressure']:.1f}），法人可能持續出貨"
    else:
        chip_direction = "中性"
        chip_desc = "買賣壓力均衡，尚無明確方向"
    
    conclusion = "bullish" if flow["direction"] == "buying" and gamma["gamma_state"] != "negative" else \
                 "bearish" if flow["direction"] == "selling" or gamma["gamma_state"] == "negative" else "neutral"
    
    confidence = min(85, 30 + flow["intensity"] // 3 + (20 if gamma["gamma_state"] != "neutral" else 0))
    
    reasoning = (
        f"【{name}（{symbol}）籌碼結構分析】\n"
        f"\n▸ WHO-WHOM-WHAT 因果框架：\n"
        f"  WHO（受限者）：{who}\n"
        f"  WHOM（被影響者）：{whom}\n"
        f"  WHAT（被迫行動）：{what}\n"
        f"  → 結論：{framework_conclusion}\n"
        f"\n▸ 籌碼方向：{chip_direction}\n"
        f"  {chip_desc}\n"
        f"\n▸ 波動率預測（1-3天）：{gamma['volatility_forecast']}\n"
        f"  日均波幅 {gamma['avg_daily_range_pct']:.2f}%，波動{'加速' if gamma['volatility_acceleration'] > 1.2 else '減速' if gamma['volatility_acceleration'] < 0.8 else '穩定'}\n"
        f"\n▸ 籌碼引力區間：{', '.join(f'{p:.0f}' for p in pinning)}\n"
        f"  現價 {current_price:.0f}，{'接近' if any(abs(current_price - p) / current_price < 0.02 for p in pinning) else '遠離'}主要引力區"
    )
    
    return {
        "conclusion": conclusion,
        "who_whom_what": {
            "who": who,
            "whom": whom,
            "what": what,
            "framework_conclusion": framework_conclusion,
        },
        "gamma": gamma,
        "institutional_flow": flow,
        "pinning_levels": pinning,
        "reasoning": reasoning,
        "confidence": confidence,
    }
