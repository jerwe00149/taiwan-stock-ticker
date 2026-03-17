"""FastAPI 主程式"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.api.routers import stocks, news, predict

app = FastAPI(
    title="台股新聞追蹤器 API",
    description="Taiwan Stock News Ticker — 台股 K線 + AI 新聞分析",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(predict.router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "台股新聞追蹤器 API", "version": "0.1.0"}
