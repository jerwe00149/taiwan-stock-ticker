"""台灣證券交易所 + 櫃買中心 資料抓取

免費公開 API，無需 API Key。
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)

TWSE_BASE = "https://www.twse.com.tw"
TPEX_BASE = "https://www.tpex.org.tw"

# 常見台股代號 → 公司名稱 / 產業
TOP_STOCKS = {
    "2330": ("台積電", "半導體", "TWSE"),
    "2317": ("鴻海", "電子零組件", "TWSE"),
    "2454": ("聯發科", "半導體", "TWSE"),
    "2412": ("中華電", "通信網路", "TWSE"),
    "2308": ("台達電", "電子零組件", "TWSE"),
    "2881": ("富邦金", "金融", "TWSE"),
    "2882": ("國泰金", "金融", "TWSE"),
    "2891": ("中信金", "金融", "TWSE"),
    "2303": ("聯電", "半導體", "TWSE"),
    "3711": ("日月光投控", "半導體", "TWSE"),
    "2886": ("兆豐金", "金融", "TWSE"),
    "1301": ("台塑", "塑膠", "TWSE"),
    "1303": ("南亞", "塑膠", "TWSE"),
    "2002": ("中鋼", "鋼鐵", "TWSE"),
    "2884": ("玉山金", "金融", "TWSE"),
    "3008": ("大立光", "光電", "TWSE"),
    "2382": ("廣達", "電腦", "TWSE"),
    "2357": ("華碩", "電腦", "TWSE"),
    "2345": ("智邦", "通信網路", "TWSE"),
    "3034": ("聯詠", "半導體", "TWSE"),
    "5274": ("信驊", "半導體", "TPEx"),
    "6669": ("緯穎", "電腦", "TPEx"),
    "3443": ("創意", "半導體", "TPEx"),
    "8069": ("元太", "光電", "TPEx"),
    "6547": ("高端疫苗", "生技", "TPEx"),
}


def fetch_twse_ohlc(symbol: str, date_str: str) -> List[Dict]:
    """從 TWSE 抓取個股日K線資料
    
    Args:
        symbol: 股票代號, e.g. '2330'
        date_str: 'YYYYMMDD' format, e.g. '20260301'
    
    Returns:
        List of {date, open, high, low, close, volume, turnover, transactions}
    """
    url = f"{TWSE_BASE}/exchangeReport/STOCK_DAY"
    params = {
        "response": "json",
        "date": date_str,
        "stockNo": symbol,
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"TWSE fetch failed for {symbol} @ {date_str}: {e}")
        return []
    
    if data.get("stat") != "OK" or "data" not in data:
        return []
    
    results = []
    for row in data["data"]:
        # row format: [日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數]
        try:
            # 民國年轉西元年
            tw_date = row[0]  # e.g. "115/03/01"
            parts = tw_date.split("/")
            y = int(parts[0]) + 1911
            m = int(parts[1])
            d = int(parts[2])
            iso_date = f"{y}-{m:02d}-{d:02d}"
            
            def parse_num(s):
                return float(str(s).replace(",", "").replace("--", "0"))
            
            results.append({
                "date": iso_date,
                "volume": parse_num(row[1]),
                "turnover": parse_num(row[2]),
                "open": parse_num(row[3]),
                "high": parse_num(row[4]),
                "low": parse_num(row[5]),
                "close": parse_num(row[6]),
                "transactions": int(parse_num(row[8])),
            })
        except (ValueError, IndexError) as e:
            logger.warning(f"Parse error for {symbol} row: {row} - {e}")
            continue
    
    return results


def fetch_tpex_ohlc(symbol: str, date_str: str) -> List[Dict]:
    """從櫃買中心抓取上櫃股日K線
    
    Args:
        symbol: 股票代號, e.g. '5274'
        date_str: 'YYYYMMDD' format → 轉為民國年 'YYY/MM'
    """
    y = int(date_str[:4]) - 1911
    m = date_str[4:6]
    tw_ym = f"{y}/{m}"
    
    url = f"{TPEX_BASE}/web/stock/aftertrading/daily_trading_info/st43_result.php"
    params = {
        "d": tw_ym,
        "stkno": symbol,
        "format": "json",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"TPEx fetch failed for {symbol} @ {tw_ym}: {e}")
        return []
    
    if not data.get("aaData"):
        return []
    
    results = []
    for row in data["aaData"]:
        try:
            tw_date = row[0]  # "115/03/01"
            parts = tw_date.split("/")
            y_val = int(parts[0]) + 1911
            iso_date = f"{y_val}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            
            def parse_num(s):
                return float(str(s).replace(",", "").replace("--", "0").replace("---", "0"))
            
            results.append({
                "date": iso_date,
                "volume": parse_num(row[1]),
                "turnover": parse_num(row[2]),
                "open": parse_num(row[3]),
                "high": parse_num(row[4]),
                "low": parse_num(row[5]),
                "close": parse_num(row[6]),
                "transactions": int(parse_num(row[8])) if len(row) > 8 else 0,
            })
        except (ValueError, IndexError):
            continue
    
    return results


def fetch_ohlc(symbol: str, start_date: str, end_date: str) -> List[Dict]:
    """抓取指定期間的日K線資料
    
    自動判斷上市/上櫃，按月抓取。
    
    Args:
        symbol: 股票代號
        start_date: 'YYYY-MM-DD'
        end_date: 'YYYY-MM-DD'
    """
    info = TOP_STOCKS.get(symbol)
    market = info[2] if info else "TWSE"
    
    fetch_fn = fetch_tpex_ohlc if market == "TPEx" else fetch_twse_ohlc
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    all_data = []
    current = start.replace(day=1)
    
    while current <= end:
        date_str = current.strftime("%Y%m01")
        logger.info(f"Fetching {symbol} for {current.strftime('%Y-%m')}")
        
        monthly = fetch_fn(symbol, date_str)
        for row in monthly:
            if start_date <= row["date"] <= end_date:
                all_data.append(row)
        
        # 下個月
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
        
        time.sleep(3)  # 禮貌性延遲，避免被擋
    
    return all_data
