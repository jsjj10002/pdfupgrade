"""
로깅 설정 모듈

구조화된 로그 포맷과 로그 레벨 관리를 제공한다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import settings


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로 (None이면 콘솔만)
        level: 로그 레벨 (None이면 settings에서 가져옴)
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 재설정 방지
    if logger.handlers:
        return logger
    
    # 로그 레벨 설정
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level))
    
    # 포맷 설정
    if settings.log_format == "json":
        # JSON 형식 로그 (구조화된 로깅)
        formatter = JsonFormatter()
    else:
        # 일반 텍스트 형식
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (지정된 경우)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if settings.log_rotation:
            # 로그 로테이션 활성화
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=settings.log_max_size_mb * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 포맷"""
        import json
        from datetime import datetime
        
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드 (extra로 전달된 값들)
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


# 기본 로거 인스턴스
default_logger = setup_logger(
    "pdfupgrade",
    log_file=settings.logs_dir / "app.log"
)


def get_logger(name: str) -> logging.Logger:
    """
    이름으로 로거 가져오기
    
    Args:
        name: 로거 이름
    
    Returns:
        로거 인스턴스
    """
    return setup_logger(name, log_file=settings.logs_dir / f"{name}.log")

