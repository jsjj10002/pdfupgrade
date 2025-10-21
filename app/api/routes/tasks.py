"""
작업 상태 라우트

작업 조회, 상태 확인, 결과 다운로드
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.schemas import TaskStatus
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.workers.task_manager import task_manager

router = APIRouter()
settings = get_settings()
logger = get_logger("api.tasks")


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    작업 상태 조회
    
    작업 ID로 작업의 현재 상태를 확인한다.
    """
    try:
        status = task_manager.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"작업을 찾을 수 없습니다: {task_id}",
            )
        
        return status
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"작업 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"작업 상태 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/tasks/{task_id}/download")
async def download_result(task_id: str):
    """
    결과 파일 다운로드
    
    완료된 작업의 결과 PDF를 다운로드한다.
    """
    try:
        status = task_manager.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"작업을 찾을 수 없습니다: {task_id}",
            )
        
        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"작업이 완료되지 않았습니다. 현재 상태: {status.status}",
            )
        
        if not status.result_file:
            raise HTTPException(
                status_code=404,
                detail="결과 파일을 찾을 수 없습니다.",
            )
        
        result_path = Path(status.result_file)
        
        if not result_path.exists():
            raise HTTPException(
                status_code=404,
                detail="결과 파일이 존재하지 않습니다.",
            )
        
        logger.info(f"결과 다운로드: {task_id}")
        
        return FileResponse(
            path=result_path,
            filename=result_path.name,
            media_type="application/pdf",
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"결과 다운로드 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"결과 다운로드 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    작업 삭제
    
    작업과 관련된 파일들을 삭제한다.
    """
    try:
        success = task_manager.delete_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"작업을 찾을 수 없습니다: {task_id}",
            )
        
        logger.info(f"작업 삭제: {task_id}")
        
        return {"message": "작업이 삭제되었습니다.", "task_id": task_id}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"작업 삭제 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"작업 삭제 중 오류가 발생했습니다: {str(e)}",
        )

