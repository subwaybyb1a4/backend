from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import init_db

# 모든 API router import (api/__init__.py에서 모아둔 구조 기준)
from app.api import (
    routes_router,
    crowding_router,
    explain_router,
    favorites_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle"""
    # Startup
    print("🚀 Starting application...")
    init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down...")


# FastAPI app 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Router 등록 (Swagger 연결 핵심)
API_PREFIX = settings.API_V1_PREFIX  # 예: "/api/v1"

app.include_router(routes_router, prefix=API_PREFIX)
app.include_router(crowding_router, prefix=API_PREFIX)
app.include_router(explain_router, prefix=API_PREFIX)
app.include_router(favorites_router, prefix=API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "안끼길 API에 오신 것을 환영합니다!",
        "version": settings.VERSION,
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


# Local 개발용 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
