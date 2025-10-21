"""
설정 관리 모듈

환경 변수를 로드하고 검증하여 애플리케이션 전반에서 사용할 수 있도록 한다.
Pydantic Settings를 사용하여 타입 안전성과 검증을 보장한다.
"""

from typing import List, Literal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션 기본 설정
    app_env: Literal["development", "production", "test"] = Field(
        default="development", alias="APP_ENV"
    )
    app_name: str = Field(default="pdfupgrade", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # API 서버 설정
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    # CORS 설정
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"], alias="ALLOWED_ORIGINS"
    )

    # 스토리지 경로
    storage_dir: Path = Field(default=Path("./storage"), alias="STORAGE_DIR")
    models_dir: Path = Field(default=Path("./app/models"), alias="MODELS_DIR")
    logs_dir: Path = Field(default=Path("./logs"), alias="LOGS_DIR")

    # GPU 설정
    use_gpu: Literal["auto", "true", "false"] = Field(default="auto", alias="USE_GPU")
    cuda_visible_devices: str = Field(default="0", alias="CUDA_VISIBLE_DEVICES")

    # Redis 설정
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    # Celery 설정
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND"
    )
    celery_max_workers: int = Field(default=2, alias="CELERY_MAX_WORKERS")
    celery_task_time_limit: int = Field(default=3600, alias="CELERY_TASK_TIME_LIMIT")

    # 파일 처리 제한
    max_file_size_mb: int = Field(default=250, alias="MAX_FILE_SIZE_MB")
    max_files_per_job: int = Field(default=10, alias="MAX_FILES_PER_JOB")
    supported_file_types: List[str] = Field(
        default=["application/pdf"], alias="SUPPORTED_FILE_TYPES"
    )

    # 업스케일 설정
    upscale_enabled: bool = Field(default=True, alias="UPSCALE_ENABLED")
    upscale_default_scale: Literal[2, 4] = Field(
        default=2, alias="UPSCALE_DEFAULT_SCALE"
    )
    upscale_face_enhance: bool = Field(default=False, alias="UPSCALE_FACE_ENHANCE")
    upscale_model_name: str = Field(
        default="RealESRGAN_x2plus", alias="UPSCALE_MODEL_NAME"
    )

    # 워터마크 제거 설정
    watermark_enabled: bool = Field(default=True, alias="WATERMARK_ENABLED")
    watermark_default_mode: Literal["auto", "template", "segment"] = Field(
        default="auto", alias="WATERMARK_DEFAULT_MODE"
    )
    watermark_detection_threshold: float = Field(
        default=0.8, alias="WATERMARK_DETECTION_THRESHOLD"
    )

    # OCR 설정
    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    ocr_engine: Literal["paddle", "tesseract"] = Field(
        default="paddle", alias="OCR_ENGINE"
    )
    ocr_default_langs: str = Field(default="kor+eng", alias="OCR_DEFAULT_LANGS")
    ocr_use_angle_cls: bool = Field(default=True, alias="OCR_USE_ANGLE_CLS")
    ocr_min_confidence: float = Field(default=0.5, alias="OCR_MIN_CONFIDENCE")

    # PDF 생성 설정
    pdf_dpi: int = Field(default=300, alias="PDF_DPI")
    pdf_output_pdfa: bool = Field(default=False, alias="PDF_OUTPUT_PDFA")
    pdf_compression: bool = Field(default=True, alias="PDF_COMPRESSION")

    # 로깅 설정
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    log_format: Literal["json", "text"] = Field(default="json", alias="LOG_FORMAT")
    log_rotation: bool = Field(default=True, alias="LOG_ROTATION")
    log_max_size_mb: int = Field(default=100, alias="LOG_MAX_SIZE_MB")

    # 보안 설정
    secret_key: str = Field(
        default="dev-secret-key-change-in-production", alias="SECRET_KEY"
    )
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")

    # 모니터링
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=False, alias="PROMETHEUS_ENABLED")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """ALLOWED_ORIGINS를 콤마로 구분된 문자열에서 리스트로 변환"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("supported_file_types", pre=True)
    def parse_supported_file_types(cls, v):
        """SUPPORTED_FILE_TYPES를 콤마로 구분된 문자열에서 리스트로 변환"""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",")]
        return v

    @validator("storage_dir", "models_dir", "logs_dir")
    def ensure_path_exists(cls, v):
        """디렉터리가 존재하지 않으면 생성"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def max_file_size_bytes(self) -> int:
        """최대 파일 크기를 바이트 단위로 반환"""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.app_env == "development"

    @property
    def input_dir(self) -> Path:
        """입력 파일 디렉터리 경로"""
        path = self.storage_dir / "input"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_dir(self) -> Path:
        """출력 파일 디렉터리 경로"""
        path = self.storage_dir / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def temp_dir(self) -> Path:
        """임시 파일 디렉터리 경로"""
        path = self.storage_dir / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_settings(self) -> None:
        """
        필수 설정 검증
        
        프로덕션 환경에서는 더 엄격한 검증 수행
        """
        errors = []

        # 프로덕션 환경 검증
        if self.is_production:
            if self.secret_key == "dev-secret-key-change-in-production":
                errors.append("SECRET_KEY must be changed in production")

            if self.debug:
                errors.append("DEBUG must be False in production")

        # Redis 연결 검증 (향후 구현)
        # if not self._check_redis_connection():
        #     errors.append("Cannot connect to Redis")

        if errors:
            raise ValueError(
                f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
            )


# 전역 설정 인스턴스
settings = Settings()

# 앱 시작 시 설정 검증
try:
    settings.validate_settings()
except ValueError as e:
    # 개발 환경에서는 경고만 출력
    if settings.is_development:
        print(f"⚠️  Configuration Warning: {e}")
    else:
        raise


# 편의를 위한 설정 값들을 모듈 레벨에서도 export
USE_GPU = settings.use_gpu
STORAGE_DIR = settings.storage_dir
MODELS_DIR = settings.models_dir
MAX_FILE_SIZE_MB = settings.max_file_size_mb

