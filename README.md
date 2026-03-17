# 台股新聞追蹤器 (TW Stock Ticker)

參考 [PokieTicker](https://github.com/owengetinfo-design/PokieTicker) 架構，專為台灣股市打造的開源新聞+股價分析工具。

## 架構

```
Frontend (React + Vite + D3.js)          Backend (FastAPI + SQLite)
+---------------------------------+      +----------------------------+
|  K線圖 (D3.js)                  |      |  /api/stocks/{sym}/ohlc    |
|  +- 新聞標記點                   |----->|  /api/news/{sym}?date=     |
|  +- 十字線 + 點擊鎖定            |      |  /api/news/{sym}/categories|
|                                  |      |                            |
|  新聞面板 (右側欄)               |<-----|  SQLite: twstock.db        |
|  +- 情緒分析排序                  |      |  +- ohlc (台股日K)         |
|  +- 利多/利空原因                 |      |  +- news_raw (中文新聞)    |
|  +- T+1/T+5 報酬率               |      |  +- layer1_results (AI分析)|
|                                  |      |                            |
|  預測面板                        |<-----|  /api/predict/{sym}/forecast|
|  +- 7天/30天預測                  |      |  +- XGBoost 模型           |
|  +- 歷史相似走勢                  |      |  +- 餘弦相似度匹配          |
+---------------------------------+      +----------------------------+
```

## 資料來源（全免費）

| 資料 | 來源 | 成本 |
|------|------|------|
| 台股 OHLC | TWSE/TPEx 開放資料 API | $0 |
| 台股新聞 | CNYES 鉅亨網 RSS / Yahoo 奇摩 | $0 |
| AI 情緒分析 | Claude Haiku Batch API | ~$0.35/1000篇 |
| 公司基本資料 | 台灣證券交易所 | $0 |

## 台股特色功能

- 🇹🇼 繁體中文介面
- 📊 支援上市 (TWSE) + 上櫃 (TPEx)
- 📰 台灣財經新聞來源（鉅亨網、工商時報、經濟日報）
- 🔍 三層 AI 分析（規則過濾 → Haiku 批次 → Sonnet 深度）
- 📈 XGBoost 預測 + 歷史走勢匹配
- 🏷️ 產業分類（半導體、金融、傳產...）

## Quick Start

```bash
git clone https://github.com/jerwe00149/taiwan-stock-ticker.git
cd taiwan-stock-ticker

# 解壓預建資料庫
gunzip twstock.db.gz

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

開啟 http://localhost:5173

## 資料管線

```
TWSE API + 新聞爬蟲 --> Layer 0 (規則過濾) --> Layer 1 (Haiku 批次) --> Layer 2 (Sonnet 深度)
  台股K線 + 中文新聞    去除無關/重複新聞       情緒分析+利多利空原因     點擊時深度分析
                       ~20% 過濾               50篇/次 API 呼叫        快取在 DB
```

## 成本

| 項目 | 成本 |
|------|------|
| 台股資料 (TWSE/TPEx) | $0 |
| Layer 1 Batch (每1000篇) | ~$0.35 |
| Layer 2 按需 (每篇) | ~$0.003 |
| 每週更新 | ~$1-2 |
