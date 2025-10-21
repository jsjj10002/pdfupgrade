"""
FastAPI 메인 애플리케이션

PDF 처리 REST API 서버
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.utils.config import get_settings
from app.utils.logger import setup_logging, get_logger
from app.api.routes import health, upload, process, tasks

settings = get_settings()
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시
    setup_logging()
    logger.info("PDF Upgrade API 서버 시작")
    logger.info(f"환경: {settings.APP_ENV}")
    logger.info(f"GPU 사용: {settings.USE_GPU}")
    
    yield
    
    # 종료 시
    logger.info("PDF Upgrade API 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="PDF Upgrade API",
    description="이미지 기반 PDF 고품질 변환 API",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.exception(f"처리되지 않은 예외: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "서버 내부 오류가 발생했습니다.",
            "detail": str(exc) if settings.APP_ENV == "development" else None,
        },
    )


# 라우터 등록
app.include_router(health.router, tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(process.router, prefix="/api", tags=["Process"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "PDF Upgrade API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )

