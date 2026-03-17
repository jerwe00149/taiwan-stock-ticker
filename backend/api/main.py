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


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path as P

FRONTEND_DIST = P(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

@app.get("/")
def root():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "台股新聞追蹤器 API", "version": "0.1.0"}
