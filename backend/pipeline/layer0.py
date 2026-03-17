"""Layer 0: 規則過濾（免費，即時）

過濾明顯無關的新聞，節省 AI 分析成本。
預計過濾 ~20% 的新聞。
"""

import re
from typing import Tuple

# 業配/廣告模式
AD_PATTERNS = [
    re.compile(r"(廣告|贊助|業配|sponsored)", re.IGNORECASE),
    re.compile(r"^\d+\s*(檔|支|個).*(推薦|首選|必買)", re.IGNORECASE),
    re.compile(r"(限時優惠|免費領取|立即申請)", re.IGNORECASE),
]

# 無關內容模式
IRRELEVANT_PATTERNS = [
    re.compile(r"(星座|運勢|塔羅|生肖)", re.IGNORECASE),
    re.compile(r"(食譜|旅遊|美食|景點)", re.IGNORECASE),
]


def filter_article(title: str, description: str, symbol: str) -> Tuple[bool, str]:
    """規則過濾
    
    Returns:
        (passed, reason) - passed=True 表示通過，進入 Layer 1
    """
    text = f"{title} {description}"
    
    # Rule 1: 標題或內容太短
    if len(title) < 5:
        return False, "title_too_short"
    
    if len(description) < 20:
        return False, "description_too_short"
    
    # Rule 2: 廣告/業配
    for pattern in AD_PATTERNS:
        if pattern.search(text):
            return False, "advertisement"
    
    # Rule 3: 無關內容
    for pattern in IRRELEVANT_PATTERNS:
        if pattern.search(title):  # 只看標題
            return False, "irrelevant_content"
    
    # Rule 4: 太多股票代號（市場概覽文，不是個股新聞）
    import re as _re
    ticker_mentions = _re.findall(r"\b\d{4}\b", text)
    if len(set(ticker_mentions)) > 8 and symbol not in title:
        return False, "market_overview_not_specific"
    
    return True, "passed"
