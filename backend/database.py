import sqlite3
from backend.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickers (
    symbol        TEXT PRIMARY KEY,    -- e.g. '2330' for TSMC
    name          TEXT,                -- e.g. '台積電'
    market        TEXT,                -- 'TWSE' or 'TPEx'
    sector        TEXT,                -- e.g. '半導體'
    last_ohlc_fetch   TEXT,
    last_news_fetch   TEXT
);

CREATE TABLE IF NOT EXISTS ohlc (
    symbol        TEXT NOT NULL,
    date          TEXT NOT NULL,
    open          REAL,
    high          REAL,
    low           REAL,
    close         REAL,
    volume        REAL,
    turnover      REAL,
    transactions  INTEGER,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS news_raw (
    id            TEXT PRIMARY KEY,
    title         TEXT,
    description   TEXT,
    publisher     TEXT,       -- 鉅亨網, 工商時報, 經濟日報...
    author        TEXT,
    published_at  TEXT,
    article_url   TEXT,
    tickers_json  TEXT,       -- JSON array of related tickers
    keywords_json TEXT        -- extracted keywords
);

CREATE TABLE IF NOT EXISTS news_ticker (
    news_id       TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    PRIMARY KEY (news_id, symbol),
    FOREIGN KEY (news_id) REFERENCES news_raw(id)
);

CREATE TABLE IF NOT EXISTS layer0_results (
    news_id       TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    passed        INTEGER NOT NULL,
    reason        TEXT,
    PRIMARY KEY (news_id, symbol)
);

CREATE TABLE IF NOT EXISTS layer1_results (
    news_id       TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    relevance     TEXT,
    key_discussion      TEXT,
    summary             TEXT,       -- 繁體中文摘要
    sentiment           TEXT,       -- positive/negative/neutral
    sentiment_score     REAL,       -- -1.0 to 1.0
    reason_growth       TEXT,       -- 利多原因
    reason_decrease     TEXT,       -- 利空原因
    PRIMARY KEY (news_id, symbol)
);

CREATE TABLE IF NOT EXISTS layer2_results (
    news_id       TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    discussion    TEXT,
    growth_reasons  TEXT,
    decrease_reasons TEXT,
    created_at    TEXT,
    PRIMARY KEY (news_id, symbol)
);

CREATE TABLE IF NOT EXISTS news_aligned (
    news_id       TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    trade_date    TEXT NOT NULL,
    return_t1     REAL,     -- T+1 報酬率
    return_t5     REAL,     -- T+5 報酬率
    PRIMARY KEY (news_id, symbol)
);

CREATE TABLE IF NOT EXISTS predictions (
    symbol        TEXT NOT NULL,
    date          TEXT NOT NULL,
    horizon       INTEGER NOT NULL,   -- 7 or 30
    predicted     REAL,
    confidence    REAL,
    features_json TEXT,
    created_at    TEXT,
    PRIMARY KEY (symbol, date, horizon)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.close()
