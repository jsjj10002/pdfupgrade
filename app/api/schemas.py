"""
API 스키마 정의 (Pydantic 모델)

요청/응답 데이터의 타입과 검증 규칙
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ===== 작업 생성 요청 =====

class ProcessOptions(BaseModel):
    """PDF 처리 옵션"""
    
    # 래스터화
    dpi: int = Field(default=300, ge=72, le=600, description="DPI (72-600)")
    
    # 전처리
    preprocess: bool = Field(default=True, description="이미지 전처리 활성화")
    deskew: bool = Field(default=True, description="기울기 보정")
    white_balance: bool = Field(default=True, description="화이트 밸런스")
    enhance_contrast: bool = Field(default=True, description="대비 향상")
    denoise: bool = Field(default=False, description="노이즈 제거")
    
    # 업스케일
    upscale: bool = Field(default=False, description="업스케일 활성화")
    upscale_scale: Literal[2, 4] = Field(default=2, description="업스케일 배율 (2x 또는 4x)")
    face_enhance: bool = Field(default=False, description="얼굴 보정 (GFPGAN)")
    
    # 워터마크 제거
    watermark: bool = Field(default=False, description="워터마크 제거 활성화")
    watermark_method: Literal["auto", "opencv"] = Field(default="auto", description="워터마크 제거 방법")
    watermark_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="워터마크 탐지 임계값")
    watermark_protect_text: bool = Field(default=True, description="본문 텍스트 보호")
    
    # OCR
    ocr: bool = Field(default=False, description="OCR 활성화")
    ocr_engine: Literal["paddle", "tesseract"] = Field(default="paddle", description="OCR 엔진")
    ocr_langs: str = Field(default="kor+eng", description="OCR 언어 (예: kor+eng)")
    ocr_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="OCR 신뢰도 임계값")
    
    # PDF 출력
    pdfa: bool = Field(default=False, description="PDF/A 형식으로 저장")
    compression: bool = Field(default=True, description="이미지 압축")


class ProcessRequest(BaseModel):
    """PDF 처리 요청"""
    options: ProcessOptions = Field(default_factory=ProcessOptions)


# ===== 작업 응답 =====

class TaskStatus(BaseModel):
    """작업 상태"""
    
    task_id: str = Field(description="작업 ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(description="작업 상태")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="진행률 (%)")
    message: Optional[str] = Field(default=None, description="상태 메시지")
    created_at: datetime = Field(description="작업 생성 시간")
    updated_at: datetime = Field(description="마지막 업데이트 시간")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")
    
    # 결과 파일 정보
    result_file: Optional[str] = Field(default=None, description="결과 파일 경로")
    file_size: Optional[int] = Field(default=None, description="파일 크기 (bytes)")
    
    # 에러 정보
    error: Optional[str] = Field(default=None, description="에러 메시지")


class TaskCreateResponse(BaseModel):
    """작업 생성 응답"""
    task_id: str = Field(description="작업 ID")
    status: str = Field(description="작업 상태")
    message: str = Field(description="메시지")


# ===== 파일 업로드 응답 =====

class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""
    filename: str = Field(description="파일명")
    size: int = Field(description="파일 크기 (bytes)")
    message: str = Field(description="메시지")


# ===== 에러 응답 =====

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(description="에러 타입")
    message: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(default=None, description="상세 정보")


# ===== 헬스 체크 =====

class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field(description="서비스 상태")
    version: str = Field(description="버전")
    timestamp: datetime = Field(description="응답 시간")
    gpu_available: bool = Field(description="GPU 사용 가능 여부")


# ===== WebSocket 메시지 =====

class WSProgressMessage(BaseModel):
    """WebSocket 진행률 메시지"""
    task_id: str
    type: Literal["progress", "status", "error", "complete"]
    progress: float = 0.0
    message: Optional[str] = None
    data: Optional[dict] = None

