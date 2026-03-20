"""多代理分析 API + Gemini AI 大腦"""

import os, json, subprocess
from fastapi import APIRouter, Query
from backend.database import get_conn
from backend.twse.client import TOP_STOCKS
from backend.agents.lead_trader import synthesize

router = APIRouter(tags=["analysis"])

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyB6VEnSlRni8fxhEVZrQbyNjm76zXQKjvU")

def gemini_analyze(symbol, name, reports, news):
    headlines = "\n".join(f"• {n.get('title','')}" for n in news[:10]) or "（無）"
    
    fund = reports.get("fundamental", {})
    tech = reports.get("technical", {})
    sent = reports.get("sentiment", {})
    
    prompt = f"""你是專業台股分析師。根據以下數據，用繁體中文給出 {name}（{symbol}）的投資建議。

技術指標：RSI {tech.get('indicators',{}).get('rsi','?')} / MACD柱 {tech.get('indicators',{}).get('macd_histogram','?')} / 5日漲跌 {tech.get('indicators',{}).get('price_change_5d','?')}%
支撐 {tech.get('support_resistance',{}).get('support','?')} / 壓力 {tech.get('support_resistance',{}).get('resistance','?')}
估值: {fund.get('valuation','?')} / 量比: {fund.get('key_metrics',{}).get('volume_ratio','?')}
恐懼貪婪: {sent.get('fear_greed_score',50)}/100 / 羊群效應: {'有' if sent.get('herding',{}).get('detected') else '無'}

近期新聞：
{headlines}

請回覆：
1. 一句話結論（看多/看空/觀望+理由）
2. 關鍵風險
3. 建議操作（進場/觀望/減碼+價位）"""

    try:
        r = subprocess.run([
            "curl", "-s",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
            "-H", "content-type: application/json",
            "-d", json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500, "thinkingConfig": {"thinkingBudget": 200}}
            })
        ], capture_output=True, text=True, timeout=20)
        resp = json.loads(r.stdout)
        return resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except:
        return ""


@router.get("/analysis/{symbol}")
def run_analysis(symbol: str, days: int = Query(120, ge=10, le=500)):
    conn = get_conn()
    
    ohlc = conn.execute("SELECT * FROM ohlc WHERE symbol=? ORDER BY date DESC LIMIT ?", [symbol, days]).fetchall()
    ohlc = [dict(r) for r in reversed(ohlc)]
    
    news = conn.execute(
        """SELECT n.*, l.sentiment, l.sentiment_score, l.summary
           FROM news_raw n JOIN news_ticker nt ON n.id=nt.news_id
           LEFT JOIN layer1_results l ON n.id=l.news_id AND l.symbol=nt.symbol
           WHERE nt.symbol=? ORDER BY n.published_at DESC LIMIT 50""", [symbol]).fetchall()
    news = [dict(r) for r in news]
    conn.close()
    
    info = TOP_STOCKS.get(symbol, ("未知", "未知", "TWSE"))
    company_info = {"name": info[0], "sector": info[1], "market": info[2]}
    
    result = synthesize(symbol, ohlc, news, company_info)
    
    # Add Gemini AI brain
    raw = result.pop("raw_reports", {})
    ai_text = gemini_analyze(symbol, info[0], raw, news)
    if ai_text:
        result["AI_Analysis"] = ai_text
        result["Analysis_Reports"]["AI_Brain"] = f"🧠 Gemini Flash AI 判斷：\n\n{ai_text}"
    
    return result

from pathlib import Path
from fastapi.responses import JSONResponse

@router.get("/ai-dashboard")
def get_ai_dashboard():
    """取得台股智能分析系統的每日報告"""
    result_path = Path.home() / ".openclaw/workspace/taiwan-stock-ticker/analysis_results.json"
    if result_path.exists():
        import json
        return json.loads(result_path.read_text())
    return {"date": "", "market": "", "stocks": {}, "ai_dashboard": "尚無分析報告，請等待每日 14:30 自動分析"}
