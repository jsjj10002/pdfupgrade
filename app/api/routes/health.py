"""
헬스 체크 라우트

서버 상태 확인
"""

from datetime import datetime
from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.utils.device import get_device
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.health")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    헬스 체크
    
    서버가 정상적으로 동작하는지 확인한다.
    """
    try:
        # GPU 사용 가능 여부 확인
        device = get_device()
        gpu_available = device.type == "cuda"
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now(),
            gpu_available=gpu_available,
        )
    
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            timestamp=datetime.now(),
            gpu_available=False,
        )

