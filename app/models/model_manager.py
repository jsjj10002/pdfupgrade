"""
AI 모델 관리 모듈

모델 가중치 다운로드, 캐싱, 버전 관리를 담당한다.
"""

from pathlib import Path
from typing import Optional
import hashlib
import json

from app.utils.logger import get_logger
from app.utils.config import settings

logger = get_logger("model_manager")


class ModelManager:
    """AI 모델 관리 클래스"""
    
    # 지원하는 모델 목록 및 메타데이터
    MODELS = {
        "RealESRGAN_x2plus": {
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
            "filename": "RealESRGAN_x2plus.pth",
            "size_mb": 64,
            "sha256": None,  # 체크섬 (선택적)
        },
        "RealESRGAN_x4plus": {
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x4plus.pth",
            "filename": "RealESRGAN_x4plus.pth",
            "size_mb": 64,
            "sha256": None,
        },
        "GFPGANv1.3": {
            "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
            "filename": "GFPGANv1.3.pth",
            "size_mb": 332,
            "sha256": None,
        },
    }
    
    def __init__(self):
        """모델 관리자 초기화"""
        self.models_dir = settings.models_dir / "weights"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.models_dir / "model_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """캐시 파일 로드"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"캐시 파일 로드 실패: {e}")
        return {}
    
    def _save_cache(self) -> None:
        """캐시 파일 저장"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"캐시 파일 저장 실패: {e}")
    
    def get_model_path(self, model_name: str, auto_download: bool = True) -> Path:
        """
        모델 파일 경로 반환
        
        파일이 없으면 자동으로 다운로드한다.
        
        Args:
            model_name: 모델 이름
            auto_download: 자동 다운로드 활성화
        
        Returns:
            모델 파일 경로
        
        Raises:
            FileNotFoundError: 모델 파일이 없고 다운로드 실패 시
        """
        if model_name not in self.MODELS:
            raise ValueError(f"지원하지 않는 모델: {model_name}")
        
        model_info = self.MODELS[model_name]
        model_path = self.models_dir / model_info["filename"]
        
        # 캐시 확인
        if model_path.exists():
            if model_name in self.cache:
                logger.debug(f"캐시된 모델 사용: {model_name}")
                return model_path
        
        # 파일 없으면 다운로드
        if not model_path.exists():
            if not auto_download:
                raise FileNotFoundError(
                    f"모델 파일을 찾을 수 없음: {model_path}\n"
                    f"다운로드: {model_info['url']}"
                )
            
            logger.info(f"모델 다운로드 시작: {model_name}")
            self.download_model(model_name)
        
        # 캐시 업데이트
        self.cache[model_name] = {
            "path": str(model_path),
            "size": model_path.stat().st_size,
        }
        self._save_cache()
        
        return model_path
    
    def download_model(self, model_name: str) -> None:
        """
        모델 다운로드
        
        Args:
            model_name: 모델 이름
        """
        import urllib.request
        
        if model_name not in self.MODELS:
            raise ValueError(f"지원하지 않는 모델: {model_name}")
        
        model_info = self.MODELS[model_name]
        url = model_info["url"]
        model_path = self.models_dir / model_info["filename"]
        
        try:
            logger.info(
                f"모델 다운로드 중: {model_name} ({model_info['size_mb']}MB)"
            )
            
            def download_progress(block_num, block_size, total_size):
                """다운로드 진행률 로그"""
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                if block_num % 100 == 0:
                    logger.debug(f"다운로드 진행: {percent:.1f}%")
            
            urllib.request.urlretrieve(url, model_path, reporthook=download_progress)
            
            # 체크섬 검증 (선택적)
            if model_info["sha256"]:
                if not self._verify_checksum(model_path, model_info["sha256"]):
                    model_path.unlink()
                    raise ValueError("체크섬 검증 실패")
            
            logger.info(f"모델 다운로드 완료: {model_path}")
        
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            if model_path.exists():
                model_path.unlink()
            raise
    
    def _verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """
        파일 체크섬 검증
        
        Args:
            file_path: 파일 경로
            expected_sha256: 예상 SHA256 해시
        
        Returns:
            검증 성공 여부
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        actual = sha256.hexdigest()
        
        if actual != expected_sha256:
            logger.error(
                f"체크섬 불일치: expected={expected_sha256}, actual={actual}"
            )
            return False
        
        return True
    
    def list_downloaded_models(self) -> list[str]:
        """
        다운로드된 모델 목록 반환
        
        Returns:
            모델 이름 리스트
        """
        downloaded = []
        
        for model_name, model_info in self.MODELS.items():
            model_path = self.models_dir / model_info["filename"]
            if model_path.exists():
                downloaded.append(model_name)
        
        return downloaded
    
    def clear_cache(self) -> None:
        """모델 캐시 삭제"""
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("모델 캐시 삭제 완료")
        self.cache = {}


# 전역 모델 관리자 인스턴스
model_manager = ModelManager()

