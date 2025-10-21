"""
이미지 업스케일 모듈

Real-ESRGAN을 이용한 고해상도 이미지 생성
"""

from typing import Optional, Literal
from pathlib import Path

import torch
import numpy as np
from PIL import Image

from app.utils.logger import get_logger
from app.utils.device import get_device, clear_gpu_cache

logger = get_logger("upscale")


class UpscaleError(Exception):
    """업스케일 관련 예외"""
    pass


class Upscaler:
    """
    Real-ESRGAN 기반 이미지 업스케일러
    
    GPU/CPU 자동 선택 및 배치 처리를 지원한다.
    """
    
    def __init__(
        self,
        scale: Literal[2, 4] = 2,
        model_name: str = "RealESRGAN_x2plus",
        device: Optional[torch.device] = None,
        tile_size: int = 512,
        face_enhance: bool = False,
    ):
        """
        Args:
            scale: 업스케일 배율 (2 또는 4)
            model_name: 모델 이름
            device: 디바이스 (None이면 자동 감지)
            tile_size: 타일 크기 (메모리 효율)
            face_enhance: 얼굴 보정 활성화 (GFPGAN)
        """
        self.scale = scale
        self.model_name = model_name
        self.device = device or get_device()
        self.tile_size = tile_size
        self.face_enhance = face_enhance
        
        self.model = None
        self.face_enhancer = None
        
        logger.info(
            f"업스케일러 초기화: scale={scale}, device={self.device}, "
            f"face_enhance={face_enhance}"
        )
    
    def load_model(self) -> None:
        """
        Real-ESRGAN 모델 로드
        
        처음 호출 시에만 모델을 로드하며, 이후에는 재사용한다.
        """
        if self.model is not None:
            logger.debug("모델이 이미 로드되어 있음")
            return
        
        try:
            # Real-ESRGAN 모델 import (지연 로딩)
            try:
                from basicsr.archs.rrdbnet_arch import RRDBNet
                from realesrgan import RealESRGANer
            except ImportError as e:
                raise UpscaleError(
                    "Real-ESRGAN 라이브러리를 찾을 수 없습니다. "
                    "설치: pip install realesrgan"
                ) from e
            
            # 모델 파라미터 설정
            if self.scale == 2:
                model = RRDBNet(
                    num_in_ch=3,
                    num_out_ch=3,
                    num_feat=64,
                    num_block=23,
                    num_grow_ch=32,
                    scale=2,
                )
                model_path = self._get_model_path("RealESRGAN_x2plus.pth")
            else:  # scale == 4
                model = RRDBNet(
                    num_in_ch=3,
                    num_out_ch=3,
                    num_feat=64,
                    num_block=23,
                    num_grow_ch=32,
                    scale=4,
                )
                model_path = self._get_model_path("RealESRGAN_x4plus.pth")
            
            # RealESRGANer 초기화
            self.model = RealESRGANer(
                scale=self.scale,
                model_path=str(model_path),
                model=model,
                tile=self.tile_size,
                tile_pad=10,
                pre_pad=0,
                half=self.device.type == "cuda",  # GPU에서 FP16 사용
                device=str(self.device),
            )
            
            logger.info(f"Real-ESRGAN 모델 로드 완료: {model_path}")
            
            # 얼굴 보정 모델 로드 (옵션)
            if self.face_enhance:
                self._load_face_enhancer()
        
        except Exception as e:
            logger.exception(f"모델 로드 실패: {e}")
            raise UpscaleError(f"모델 로드 실패: {e}") from e
    
    def _load_face_enhancer(self) -> None:
        """GFPGAN 얼굴 보정 모델 로드"""
        try:
            from gfpgan import GFPGANer
            
            model_path = self._get_model_path("GFPGANv1.3.pth")
            
            self.face_enhancer = GFPGANer(
                model_path=str(model_path),
                upscale=1,  # 얼굴만 보정, 전체 업스케일은 ESRGAN이 담당
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=None,
                device=str(self.device),
            )
            
            logger.info(f"GFPGAN 모델 로드 완료: {model_path}")
        
        except ImportError as e:
            logger.warning(f"GFPGAN을 찾을 수 없어 얼굴 보정 비활성화: {e}")
            self.face_enhance = False
        except Exception as e:
            logger.warning(f"얼굴 보정 모델 로드 실패, 비활성화: {e}")
            self.face_enhance = False
    
    def _get_model_path(self, filename: str) -> Path:
        """
        모델 가중치 파일 경로 반환
        
        파일이 없으면 자동 다운로드를 시도한다.
        
        Args:
            filename: 모델 파일명
        
        Returns:
            모델 파일 경로
        """
        from app.utils.config import settings
        
        models_dir = settings.models_dir / "weights"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = models_dir / filename
        
        if not model_path.exists():
            logger.info(f"모델 파일이 없음, 다운로드 시도: {filename}")
            self._download_model(filename, model_path)
        
        return model_path
    
    def _download_model(self, filename: str, save_path: Path) -> None:
        """
        모델 가중치 다운로드
        
        Args:
            filename: 모델 파일명
            save_path: 저장 경로
        """
        import urllib.request
        
        # 모델 다운로드 URL (GitHub Releases)
        base_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1"
        
        url_map = {
            "RealESRGAN_x2plus.pth": f"{base_url}/RealESRGAN_x2plus.pth",
            "RealESRGAN_x4plus.pth": f"{base_url}/RealESRGAN_x4plus.pth",
            "GFPGANv1.3.pth": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
        }
        
        if filename not in url_map:
            raise UpscaleError(f"알 수 없는 모델 파일: {filename}")
        
        url = url_map[filename]
        
        try:
            logger.info(f"모델 다운로드 중: {url}")
            
            def download_progress(block_num, block_size, total_size):
                """다운로드 진행률 표시"""
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                if block_num % 100 == 0:  # 100블록마다 로그
                    logger.debug(f"다운로드 진행: {percent:.1f}%")
            
            urllib.request.urlretrieve(url, save_path, reporthook=download_progress)
            
            logger.info(f"모델 다운로드 완료: {save_path}")
        
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            if save_path.exists():
                save_path.unlink()
            raise UpscaleError(
                f"모델 다운로드 실패: {e}\n"
                f"수동으로 다운로드: {url} → {save_path}"
            ) from e
    
    def upscale(self, image: Image.Image) -> Image.Image:
        """
        이미지 업스케일
        
        Args:
            image: 입력 이미지 (PIL Image)
        
        Returns:
            업스케일된 이미지 (PIL Image)
        
        Raises:
            UpscaleError: 업스케일 실패 시
        """
        # 모델 로드 (최초 1회)
        self.load_model()
        
        try:
            # PIL Image → numpy 배열
            img_np = np.array(image)
            
            # RGB → BGR (OpenCV 포맷)
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                img_np = img_np[:, :, ::-1]
            
            logger.debug(f"업스케일 시작: {img_np.shape}")
            
            # Real-ESRGAN 업스케일
            output, _ = self.model.enhance(img_np, outscale=self.scale)
            
            # 얼굴 보정 (옵션)
            if self.face_enhance and self.face_enhancer is not None:
                logger.debug("얼굴 보정 적용")
                _, _, output = self.face_enhancer.enhance(
                    output,
                    has_aligned=False,
                    only_center_face=False,
                    paste_back=True,
                )
            
            # BGR → RGB
            if len(output.shape) == 3 and output.shape[2] == 3:
                output = output[:, :, ::-1]
            
            # numpy 배열 → PIL Image
            result = Image.fromarray(output)
            
            logger.debug(f"업스케일 완료: {result.size}")
            
            # GPU 메모리 정리
            if self.device.type == "cuda":
                clear_gpu_cache()
            
            return result
        
        except Exception as e:
            logger.exception(f"업스케일 실패: {e}")
            
            # GPU 메모리 부족 에러 처리
            if "out of memory" in str(e).lower():
                logger.warning("GPU 메모리 부족, 타일 크기를 줄여 재시도 권장")
                raise UpscaleError(
                    f"GPU 메모리 부족: {e}\n"
                    f"타일 크기를 줄이거나 CPU 모드를 사용하세요."
                ) from e
            
            raise UpscaleError(f"업스케일 실패: {e}") from e
    
    def upscale_batch(
        self,
        images: list[Image.Image],
        progress_callback: Optional[callable] = None,
    ) -> list[Image.Image]:
        """
        여러 이미지 배치 업스케일
        
        Args:
            images: 입력 이미지 리스트
            progress_callback: 진행률 콜백 함수 (idx, total)
        
        Returns:
            업스케일된 이미지 리스트
        """
        results = []
        total = len(images)
        
        logger.info(f"배치 업스케일 시작: {total}개 이미지")
        
        for idx, img in enumerate(images):
            try:
                result = self.upscale(img)
                results.append(result)
                
                if progress_callback:
                    progress_callback(idx + 1, total)
                
                logger.debug(f"업스케일 진행: {idx+1}/{total}")
            
            except Exception as e:
                logger.error(f"이미지 {idx+1} 업스케일 실패: {e}")
                # 실패 시 원본 이미지 사용
                results.append(img)
        
        logger.info(f"배치 업스케일 완료: {len(results)}개")
        
        return results
    
    def __del__(self):
        """소멸자: GPU 메모리 정리"""
        if self.device.type == "cuda":
            clear_gpu_cache()


def upscale_image_simple(
    image: Image.Image,
    scale: Literal[2, 4] = 2,
    face_enhance: bool = False,
) -> Image.Image:
    """
    간단한 이미지 업스케일 함수 (헬퍼)
    
    Args:
        image: 입력 이미지
        scale: 업스케일 배율
        face_enhance: 얼굴 보정 활성화
    
    Returns:
        업스케일된 이미지
    """
    upscaler = Upscaler(scale=scale, face_enhance=face_enhance)
    return upscaler.upscale(image)

