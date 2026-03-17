"""Layer 1: Claude Haiku 批次分析

策略:
1. 50 篇新聞打包成 1 次 API 呼叫
2. 回傳結構化 JSON — 繁體中文
3. 包含情緒分析 + 利多/利空原因
"""

import json
import logging
from typing import List, Dict, Any

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 50
MAX_OUTPUT_TOKENS = 8192

SYSTEM_PROMPT = """你是台灣股市新聞分析師。分析以下新聞對指定股票的影響。

對每篇新聞回傳 JSON:
{
  "id": "新聞ID",
  "relevance": "high/medium/low",
  "sentiment": "positive/negative/neutral",
  "sentiment_score": -1.0 到 1.0,
  "summary": "一句話摘要（繁體中文）",
  "reason_growth": "利多原因（若有）",
  "reason_decrease": "利空原因（若有）",
  "key_discussion": "關鍵討論點"
}

規則:
- sentiment_score: -1.0 極度利空, 0 中性, 1.0 極度利多
- 只分析對該股票的直接影響
- 摘要用繁體中文，簡潔有力
- 如果新聞與該股票無關，relevance 設為 "low"
"""


def analyze_batch(articles: List[Dict], symbol: str, company_name: str) -> List[Dict]:
    """批次分析新聞
    
    Args:
        articles: [{id, title, description}, ...]
        symbol: 股票代號, e.g. '2330'
        company_name: 公司名稱, e.g. '台積電'
    
    Returns:
        List of analysis results
    """
    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key, skipping Layer 1")
        return []
    
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    # 打包新聞
    news_block = []
    for i, art in enumerate(articles[:BATCH_SIZE]):
        news_block.append(
            f"[{i+1}] ID: {art['id']}\n"
            f"標題: {art['title']}\n"
            f"內容: {art.get('description', '')[:300]}\n"
        )
    
    user_prompt = (
        f"股票: {symbol} ({company_name})\n\n"
        f"以下 {len(news_block)} 篇新聞，請逐篇分析:\n\n"
        + "\n---\n".join(news_block)
        + "\n\n請回傳 JSON 陣列，每篇一個物件。"
    )
    
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        
        text = response.content[0].text
        # 解析 JSON
        import re
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
    except Exception as e:
        logger.error(f"Layer 1 analysis failed: {e}")
    
    return []
