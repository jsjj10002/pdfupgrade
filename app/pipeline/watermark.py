"""
워터마크 제거 모듈

워터마크 탐지 및 인페인팅을 통한 제거
"""

from typing import Optional, Literal, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.utils.logger import get_logger
from app.utils.device import get_device

logger = get_logger("watermark")


class WatermarkRemovalError(Exception):
    """워터마크 제거 관련 예외"""
    pass


class WatermarkRemover:
    """
    워터마크 탐지 및 제거 클래스
    
    다양한 방법으로 워터마크를 탐지하고 인페인팅으로 제거한다.
    """
    
    def __init__(
        self,
        method: Literal["auto", "template", "opencv", "lama"] = "auto",
        detection_threshold: float = 0.8,
        protect_text: bool = True,
    ):
        """
        Args:
            method: 워터마크 제거 방법
                - auto: 자동 선택
                - template: 템플릿 매칭 (반복 패턴)
                - opencv: OpenCV 인페인팅 (빠름)
                - lama: LaMa 인페인팅 (고품질, 느림)
            detection_threshold: 워터마크 탐지 임계값
            protect_text: 본문 텍스트 보호
        """
        self.method = method
        self.detection_threshold = detection_threshold
        self.protect_text = protect_text
        
        self.lama_model = None
        
        logger.info(
            f"워터마크 제거기 초기화: method={method}, "
            f"threshold={detection_threshold}, protect_text={protect_text}"
        )
    
    def remove(self, image: Image.Image, mask: Optional[np.ndarray] = None) -> Image.Image:
        """
        워터마크 제거
        
        Args:
            image: 입력 이미지 (PIL Image)
            mask: 워터마크 마스크 (선택적, None이면 자동 탐지)
        
        Returns:
            워터마크가 제거된 이미지 (PIL Image)
        
        Raises:
            WatermarkRemovalError: 워터마크 제거 실패 시
        """
        try:
            # PIL Image → numpy 배열
            img_np = np.array(image)
            
            # 마스크 생성 (제공되지 않은 경우)
            if mask is None:
                logger.debug("워터마크 자동 탐지 시작")
                mask = self.detect_watermark(img_np)
            
            # 마스크가 비어있으면 원본 반환
            if mask is None or np.sum(mask) == 0:
                logger.debug("워터마크를 찾을 수 없음, 원본 반환")
                return image
            
            logger.debug(f"워터마크 마스크 크기: {np.sum(mask > 0)} 픽셀")
            
            # 본문 텍스트 보호 (선택적)
            if self.protect_text:
                mask = self._protect_text_regions(img_np, mask)
            
            # 인페인팅 방법 선택
            if self.method == "auto":
                # 마스크 크기에 따라 자동 선택
                mask_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
                if mask_ratio < 0.1:
                    method = "opencv"  # 작은 영역은 OpenCV (빠름)
                else:
                    method = "opencv"  # LaMa는 선택적으로 사용
            else:
                method = self.method
            
            logger.debug(f"인페인팅 방법: {method}")
            
            # 인페인팅 실행
            if method == "lama":
                result = self._inpaint_lama(img_np, mask)
            else:  # opencv
                result = self._inpaint_opencv(img_np, mask)
            
            # numpy 배열 → PIL Image
            return Image.fromarray(result)
        
        except Exception as e:
            logger.exception(f"워터마크 제거 실패: {e}")
            raise WatermarkRemovalError(f"워터마크 제거 실패: {e}") from e
    
    def detect_watermark(self, img: np.ndarray) -> np.ndarray:
        """
        워터마크 자동 탐지
        
        다양한 방법을 조합하여 워터마크 영역을 탐지한다.
        
        Args:
            img: 입력 이미지 (numpy 배열, RGB)
        
        Returns:
            워터마크 마스크 (0 또는 255, grayscale)
        """
        h, w = img.shape[:2]
        
        # 1. 반투명 영역 탐지
        mask_alpha = self._detect_translucent_regions(img)
        
        # 2. 색상 이상 영역 탐지
        mask_color = self._detect_color_anomalies(img)
        
        # 3. 고주파 패턴 탐지
        mask_pattern = self._detect_high_frequency_patterns(img)
        
        # 마스크 통합 (OR 연산)
        combined_mask = np.maximum(mask_alpha, mask_color)
        combined_mask = np.maximum(combined_mask, mask_pattern)
        
        # 모폴로지 연산으로 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        return combined_mask
    
    def _detect_translucent_regions(self, img: np.ndarray) -> np.ndarray:
        """반투명 영역 탐지 (워터마크는 종종 반투명)"""
        # HSV 변환
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # 채도가 낮고 명도가 높은 영역 (반투명 효과)
        _, s, v = cv2.split(hsv)
        
        # 낮은 채도 + 중간~높은 명도
        low_saturation = s < 50
        mid_to_high_value = (v > 150) & (v < 240)
        
        mask = (low_saturation & mid_to_high_value).astype(np.uint8) * 255
        
        return mask
    
    def _detect_color_anomalies(self, img: np.ndarray) -> np.ndarray:
        """색상 이상 영역 탐지"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 적응형 임계값
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 엣지 검출
        edges = cv2.Canny(gray, 50, 150)
        
        # 통합
        mask = cv2.bitwise_or(adaptive, edges)
        
        # 너무 많은 영역이 감지되면 무시 (전체 텍스트가 아닌 워터마크만)
        white_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
        if white_ratio > 0.3:
            return np.zeros_like(mask)
        
        return mask
    
    def _detect_high_frequency_patterns(self, img: np.ndarray) -> np.ndarray:
        """고주파 패턴 탐지 (반복 로고/텍스트)"""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # FFT로 주파수 분석
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 고주파 영역 마스크
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        
        # 중심에서 멀리 떨어진 고주파만 추출
        mask_fft = np.zeros((rows, cols, 2), np.uint8)
        r = 30
        center = [crow, ccol]
        x, y = np.ogrid[:rows, :cols]
        mask_area = (x - center[0]) ** 2 + (y - center[1]) ** 2 >= r**2
        mask_fft[mask_area] = 1
        
        # 역변환
        fshift = dft_shift * mask_fft
        f_ishift = np.fft.ifftshift(fshift)
        img_back = cv2.idft(f_ishift)
        img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])
        
        # 정규화 및 임계값
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)
        _, mask = cv2.threshold(img_back.astype(np.uint8), 30, 255, cv2.THRESH_BINARY)
        
        return mask
    
    def _protect_text_regions(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        본문 텍스트 영역 보호
        
        워터마크 마스크에서 본문 텍스트 영역을 제외한다.
        """
        # MSER(Maximally Stable Extremal Regions)로 텍스트 영역 탐지
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        # 텍스트 영역 마스크 생성
        text_mask = np.zeros_like(mask)
        for region in regions:
            # 작은 영역만 텍스트로 간주
            if len(region) < 1000:
                text_mask[region[:, 1], region[:, 0]] = 255
        
        # 텍스트 영역 확장 (안전 마진)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        text_mask = cv2.dilate(text_mask, kernel, iterations=1)
        
        # 워터마크 마스크에서 텍스트 영역 제외
        protected_mask = cv2.bitwise_and(mask, cv2.bitwise_not(text_mask))
        
        return protected_mask
    
    def _inpaint_opencv(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        OpenCV 인페인팅
        
        빠르지만 품질은 중간 수준
        """
        # RGB → BGR (OpenCV 포맷)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # 인페인팅 (Telea 알고리즘)
        result_bgr = cv2.inpaint(img_bgr, mask, 3, cv2.INPAINT_TELEA)
        
        # BGR → RGB
        result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
        
        return result_rgb
    
    def _inpaint_lama(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        LaMa 인페인팅
        
        고품질이지만 느림 (향후 구현)
        """
        logger.warning("LaMa 인페인팅은 향후 구현 예정, OpenCV로 대체")
        return self._inpaint_opencv(img, mask)
    
    def remove_batch(
        self,
        images: list[Image.Image],
        progress_callback: Optional[callable] = None,
    ) -> list[Image.Image]:
        """
        여러 이미지 배치 워터마크 제거
        
        Args:
            images: 입력 이미지 리스트
            progress_callback: 진행률 콜백 함수 (idx, total)
        
        Returns:
            워터마크가 제거된 이미지 리스트
        """
        results = []
        total = len(images)
        
        logger.info(f"배치 워터마크 제거 시작: {total}개 이미지")
        
        for idx, img in enumerate(images):
            try:
                result = self.remove(img)
                results.append(result)
                
                if progress_callback:
                    progress_callback(idx + 1, total)
                
                logger.debug(f"워터마크 제거 진행: {idx+1}/{total}")
            
            except Exception as e:
                logger.error(f"이미지 {idx+1} 워터마크 제거 실패: {e}")
                # 실패 시 원본 이미지 사용
                results.append(img)
        
        logger.info(f"배치 워터마크 제거 완료: {len(results)}개")
        
        return results


def remove_watermark_simple(
    image: Image.Image,
    method: Literal["auto", "opencv"] = "auto",
) -> Image.Image:
    """
    간단한 워터마크 제거 함수 (헬퍼)
    
    Args:
        image: 입력 이미지
        method: 제거 방법
    
    Returns:
        워터마크가 제거된 이미지
    """
    remover = WatermarkRemover(method=method)
    return remover.remove(image)

