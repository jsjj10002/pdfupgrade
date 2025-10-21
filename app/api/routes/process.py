"""
PDF 처리 라우트

PDF 처리 작업 생성 및 관리
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.api.schemas import ProcessRequest, TaskCreateResponse
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.workers.task_manager import task_manager

router = APIRouter()
settings = get_settings()
logger = get_logger("api.process")


@router.post("/process/{filename}", response_model=TaskCreateResponse)
async def process_pdf(filename: str, request: ProcessRequest):
    """
    PDF 처리 작업 생성
    
    업로드된 PDF 파일에 대한 처리 작업을 생성한다.
    """
    try:
        # 파일 존재 확인
        upload_dir = Path(settings.STORAGE_DIR) / "uploads"
        input_file = upload_dir / filename
        
        if not input_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"파일을 찾을 수 없습니다: {filename}",
            )
        
        # 작업 생성
        task_id = task_manager.create_task(
            input_file=str(input_file),
            options=request.options.model_dump(),
        )
        
        logger.info(f"작업 생성: {task_id} (파일: {filename})")
        
        return TaskCreateResponse(
            task_id=task_id,
            status="pending",
            message="작업이 생성되었습니다. 처리가 곧 시작됩니다.",
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"작업 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"작업 생성 중 오류가 발생했습니다: {str(e)}",
        )

