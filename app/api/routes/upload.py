"""
파일 업로드 라우트

PDF 파일 업로드 처리
"""

from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.api.schemas import FileUploadResponse
from app.utils.config import get_settings
from app.utils.logger import get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger("api.upload")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    파일 업로드
    
    PDF 파일을 업로드하고 임시 저장한다.
    """
    try:
        # 파일 타입 확인
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="PDF 파일만 업로드 가능합니다.",
            )
        
        # 파일 크기 확인
        contents = await file.read()
        file_size = len(contents)
        
        max_size = settings.FILE_SIZE_LIMIT_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기는 {settings.FILE_SIZE_LIMIT_MB}MB를 초과할 수 없습니다.",
            )
        
        # 임시 디렉터리에 저장
        upload_dir = Path(settings.STORAGE_DIR) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        # 파일명 중복 시 번호 추가
        counter = 1
        while file_path.exists():
            stem = Path(file.filename).stem
            suffix = Path(file.filename).suffix
            file_path = upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"파일 업로드 완료: {file_path.name} ({file_size} bytes)")
        
        return FileUploadResponse(
            filename=file_path.name,
            size=file_size,
            message="파일이 성공적으로 업로드되었습니다.",
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"파일 업로드 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}",
        )

