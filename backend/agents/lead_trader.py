"""⚖️ 交易經理 (Lead Trader & Synthesizer)

綜合4個Agent的分析，產出最終交易決策。
"""

from typing import Dict, Any
from backend.agents import fundamental, technical, positioning, sentiment


def _bull_bear_debate(reports: Dict) -> str:
    """多空辯論（當各Agent結論分歧時觸發）"""
    conclusions = {
        "fundamental": reports["fundamental"]["conclusion"],
        "technical": reports["technical"]["conclusion"],
        "positioning": reports["positioning"]["conclusion"],
        "sentiment": reports["sentiment"]["conclusion"],
    }
    
    bulls = [k for k, v in conclusions.items() if v in ("bullish", "extreme_greed")]
    bears = [k for k, v in conclusions.items() if v in ("bearish", "extreme_fear")]
    
    agent_names = {
        "fundamental": "基本面分析師",
        "technical": "技術面分析師",
        "positioning": "籌碼分析師",
        "sentiment": "情緒分析師",
    }
    
    debate = "═══ 多空辯論 (Bull vs. Bear Debate) ═══\n\n"
    
    if bulls:
        debate += "🐂 多方觀點：\n"
        for b in bulls:
            debate += f"  • {agent_names[b]}：{reports[b].get('reasoning', '').split(chr(10))[-1].strip()}\n"
    
    if bears:
        debate += "\n🐻 空方觀點：\n"
        for b in bears:
            debate += f"  • {agent_names[b]}：{reports[b].get('reasoning', '').split(chr(10))[-1].strip()}\n"
    
    neutrals = [k for k in conclusions if k not in bulls and k not in bears]
    if neutrals:
        debate += "\n⚖️ 中立觀點：\n"
        for n in neutrals:
            debate += f"  • {agent_names[n]}：維持觀望\n"
    
    return debate


def synthesize(symbol: str, ohlc_data: list, news_data: list, company_info: dict) -> Dict[str, Any]:
    """執行多代理分析並綜合決策"""
    
    # 並行分析（在實際部署中可用 asyncio）
    fund_report = fundamental.analyze(symbol, ohlc_data, news_data, company_info)
    tech_report = technical.analyze(symbol, ohlc_data, company_info)
    pos_report = positioning.analyze(symbol, ohlc_data, company_info)
    sent_report = sentiment.analyze(symbol, ohlc_data, news_data, company_info)
    
    reports = {
        "fundamental": fund_report,
        "technical": tech_report,
        "positioning": pos_report,
        "sentiment": sent_report,
    }
    
    # 收集各Agent結論
    conclusions = {
        "fundamental": fund_report["conclusion"],
        "technical": tech_report["conclusion"],
        "positioning": pos_report["conclusion"],
        "sentiment": sent_report["conclusion"],
    }
    
    fg_score = sent_report.get("fear_greed_score", 50)
    gamma_state = pos_report.get("gamma", {}).get("gamma_state", "neutral")
    
    # === 核心決策邏輯（側重情緒交易）===
    
    action = "HOLD"
    confidence = 50
    reasoning_parts = []
    risk_mgmt = []
    
    # 策略1: 極度恐慌 + 基本面未損 → 逆勢作多
    if fg_score <= 25 and fund_report["conclusion"] != "bearish":
        action = "BUY"
        confidence = 70
        reasoning_parts.append(
            "🔑 情緒極度恐慌（{}/100），但基本面未受損（{}），符合逆勢作多策略".format(
                fg_score, fund_report.get("valuation", "unknown")
            )
        )
        
        # 結合 Gamma
        if gamma_state == "negative":
            reasoning_parts.append(
                "⚠️ 市場處於負 Gamma 狀態，波動將被放大，需設嚴格停損"
            )
            support = tech_report.get("support_resistance", {}).get("support", 0)
            if support:
                risk_mgmt.append(f"停損設於技術支撐 {support:.0f} 下方 1%")
            confidence = min(confidence + 10, 85)
        
        if tech_report["conclusion"] == "bullish":
            reasoning_parts.append("✅ 技術面同步確認多頭，增強買入信心")
            confidence = min(confidence + 10, 90)
    
    # 策略2: 極度貪婪 + 基本面高估 → 減碼
    elif fg_score >= 80 and fund_report.get("valuation") == "overvalued":
        action = "SELL"
        confidence = 65
        reasoning_parts.append(
            "🔑 情緒極度貪婪（{}/100）且股價偏高估，獲利了結壓力大".format(fg_score)
        )
        
        if pos_report.get("herding", {}).get("detected"):
            reasoning_parts.append("⚠️ 偵測到羊群效應，情緒反轉風險高")
            confidence = min(confidence + 10, 85)
    
    # 策略3: 多數 Agent 看多
    elif sum(1 for v in conclusions.values() if v in ("bullish",)) >= 3:
        action = "BUY"
        confidence = 60 + sum(r.get("confidence", 50) for r in reports.values()) // 8
        reasoning_parts.append("多數分析師（{}/4）看多，形成共振".format(
            sum(1 for v in conclusions.values() if v in ("bullish",))
        ))
    
    # 策略4: 多數 Agent 看空
    elif sum(1 for v in conclusions.values() if v in ("bearish", "extreme_fear")) >= 3:
        action = "SELL"
        confidence = 55 + sum(r.get("confidence", 50) for r in reports.values()) // 8
        reasoning_parts.append("多數分析師（{}/4）看空，建議減碼".format(
            sum(1 for v in conclusions.values() if v in ("bearish", "extreme_fear"))
        ))
    
    # 其他: HOLD
    else:
        action = "HOLD"
        confidence = 40
        reasoning_parts.append("各面向訊號分歧，建議暫時觀望")
    
    # 檢查是否需要多空辯論
    bulls = sum(1 for v in conclusions.values() if v in ("bullish",))
    bears = sum(1 for v in conclusions.values() if v in ("bearish", "extreme_fear"))
    
    debate = None
    if bulls >= 2 and bears >= 2:
        debate = _bull_bear_debate(reports)
        reasoning_parts.append("⚔️ 多空分歧嚴重，已啟動多空辯論")
    
    # 風險管理
    if not risk_mgmt:
        support = tech_report.get("support_resistance", {}).get("support", 0)
        if support and action == "BUY":
            risk_mgmt.append(f"停損：{support:.0f}（技術支撐）")
            risk_mgmt.append("部位控管：首次進場建議半倉，確認突破再加碼")
        elif action == "SELL":
            resistance = tech_report.get("support_resistance", {}).get("resistance", 0)
            if resistance:
                risk_mgmt.append(f"停利：{resistance:.0f}（技術壓力）")
            risk_mgmt.append("分批減碼，保留 30% 觀察後續走勢")
        else:
            risk_mgmt.append("觀望中，無需調整部位")
    
    confidence = min(95, max(10, confidence))
    
    return {
        "Analysis_Reports": {
            "Fundamental": fund_report["reasoning"],
            "Technical": tech_report["reasoning"],
            "Positioning_and_Chips": pos_report["reasoning"],
            "Market_Sentiment": f"Score: {fg_score}/100, {sent_report.get('sentiment_label', '')}\n{sent_report['reasoning']}",
        },
        "Trade_Decision": {
            "Action": action,
            "Confidence_Level": f"{confidence}%",
            "Reasoning": "\n".join(reasoning_parts),
            "Risk_Management": "\n".join(risk_mgmt),
        },
        "Agent_Conclusions": conclusions,
        "Fear_Greed_Score": fg_score,
        "Bull_Bear_Debate": debate,
        "raw_reports": reports,
    }

import subprocess

GEMINI_KEY = "AIzaSyC9VkJPwATispujOPL3Y5wjNeFSa1JfTq4"

def ai_analysis(symbol: str, company_info: dict, reports: dict, news_data: list) -> str:
    """Gemini Flash 讀新聞 + 數據後給出 AI 判斷"""
    name = company_info.get("name", symbol)
    
    # Collect top news headlines
    headlines = []
    for n in news_data[:10]:
        title = n.get("title", "")
        if title:
            headlines.append(title)
    
    news_text = "\n".join(f"• {h}" for h in headlines) if headlines else "（無近期新聞）"
    
    # Get key metrics from agents
    fund = reports["fundamental"]
    tech = reports["technical"]
    sent = reports["sentiment"]
    pos = reports["positioning"]
    
    prompt = f"""你是專業台股分析師。請根據以下數據，用繁體中文給出 {name}（{symbol}）的投資建議。

📊 技術指標：
- RSI: {tech.get('indicators',{}).get('rsi','N/A')}
- MACD柱狀體: {tech.get('indicators',{}).get('macd_histogram','N/A')}
- 布林帶寬: {tech.get('indicators',{}).get('bollinger_bandwidth','N/A')}%
- 5日漲跌: {tech.get('indicators',{}).get('price_change_5d','N/A')}%
- 支撐: {tech.get('support_resistance',{}).get('support','N/A')} / 壓力: {tech.get('support_resistance',{}).get('resistance','N/A')}

📈 基本面：
- 估值: {fund.get('valuation','N/A')}
- 股價vs120日均線: {fund.get('key_metrics',{}).get('price_vs_ma120_pct','N/A')}%
- 量比: {fund.get('key_metrics',{}).get('volume_ratio','N/A')}

🔥 情緒面：
- 恐懼貪婪指數: {sent.get('fear_greed_score',50)}/100
- 羊群效應: {'有' if sent.get('herding',{}).get('detected') else '無'}

📰 近期新聞：
{news_text}

請回覆（100字內）：
1. 一句話結論（看多/看空/觀望）
2. 最關鍵的理由
3. 建議操作策略"""

    try:
        result = subprocess.run([
            "curl", "-s",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
            "-H", "content-type: application/json",
            "-d", json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
            })
        ], capture_output=True, text=True, timeout=15)
        
        resp = json.loads(result.stdout)
        return resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except:
        return ""


# Patch synthesize to include AI analysis
_original_synthesize = synthesize

def synthesize_with_ai(symbol, ohlc_data, news_data, company_info):
    result = _original_synthesize(symbol, ohlc_data, news_data, company_info)
    
    # Add Gemini AI analysis
    try:
        ai_text = ai_analysis(symbol, company_info, result.get("raw_reports", {}), news_data)
        if ai_text:
            result["AI_Analysis"] = ai_text
            result["Analysis_Reports"]["AI_Brain"] = f"🧠 Gemini Flash AI 分析：\n{ai_text}"
    except:
        pass
    
    # Remove raw_reports before returning
    result.pop("raw_reports", None)
    return result

# Replace
synthesize = synthesize_with_ai
