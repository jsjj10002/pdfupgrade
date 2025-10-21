"""
이미지 전처리 모듈

이미지 품질 개선을 위한 전처리 작업을 수행한다.
"""

from typing import Optional

import cv2
import numpy as np
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger("preprocess")


def auto_enhance(
    image: Image.Image,
    options: Optional[dict] = None,
) -> Image.Image:
    """
    이미지 자동 품질 개선
    
    다음 전처리 작업을 순차적으로 수행:
    1. 회전 보정 (디스큐)
    2. 화이트밸런스 조정
    3. 대비 향상 (CLAHE)
    4. 노이즈 제거
    
    Args:
        image: 입력 이미지 (PIL Image)
        options: 전처리 옵션
            - deskew: 회전 보정 활성화 (기본값: True)
            - white_balance: 화이트밸런스 조정 (기본값: True)
            - enhance_contrast: 대비 향상 (기본값: True)
            - denoise: 노이즈 제거 (기본값: False, 느림)
    
    Returns:
        전처리된 이미지 (PIL Image)
    """
    if options is None:
        options = {}
    
    # 옵션 기본값
    do_deskew = options.get("deskew", True)
    do_white_balance = options.get("white_balance", True)
    do_enhance_contrast = options.get("enhance_contrast", True)
    do_denoise = options.get("denoise", False)
    
    # PIL → OpenCV (numpy 배열)
    img_np = np.array(image)
    
    logger.debug(f"전처리 시작: {img_np.shape}")
    
    # 1. 회전 보정
    if do_deskew:
        img_np = deskew_image(img_np)
    
    # 2. 화이트밸런스
    if do_white_balance:
        img_np = adjust_white_balance(img_np)
    
    # 3. 대비 향상
    if do_enhance_contrast:
        img_np = enhance_contrast(img_np)
    
    # 4. 노이즈 제거 (선택적, 느림)
    if do_denoise:
        img_np = remove_noise(img_np)
    
    # OpenCV → PIL
    result = Image.fromarray(img_np)
    
    logger.debug(f"전처리 완료: {result.size}")
    
    return result


def deskew_image(img: np.ndarray) -> np.ndarray:
    """
    이미지 회전 보정 (디스큐)
    
    Args:
        img: 입력 이미지 (numpy 배열)
    
    Returns:
        회전 보정된 이미지
    """
    # 그레이스케일 변환
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # 이진화
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 회전 각도 추정 (Hough 변환)
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) == 0:
        return img
    
    angle = cv2.minAreaRect(coords)[-1]
    
    # 각도 보정 (-45도 ~ 45도 범위로 조정)
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90
    
    # 각도가 매우 작으면 회전하지 않음
    if abs(angle) < 0.5:
        return img
    
    # 이미지 회전
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    
    logger.debug(f"이미지 회전 보정: {angle:.2f}도")
    
    return rotated


def adjust_white_balance(img: np.ndarray) -> np.ndarray:
    """
    화이트밸런스 조정 (그레이월드 알고리즘)
    
    Args:
        img: 입력 이미지 (RGB, numpy 배열)
    
    Returns:
        화이트밸런스 조정된 이미지
    """
    if len(img.shape) != 3:
        return img
    
    # 각 채널의 평균 계산
    r_mean = np.mean(img[:, :, 0])
    g_mean = np.mean(img[:, :, 1])
    b_mean = np.mean(img[:, :, 2])
    
    # 그레이 평균
    gray_mean = (r_mean + g_mean + b_mean) / 3
    
    # 스케일 팩터 계산
    r_scale = gray_mean / r_mean if r_mean > 0 else 1.0
    g_scale = gray_mean / g_mean if g_mean > 0 else 1.0
    b_scale = gray_mean / b_mean if b_mean > 0 else 1.0
    
    # 채널별 스케일 적용
    result = img.astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] * r_scale, 0, 255)
    result[:, :, 1] = np.clip(result[:, :, 1] * g_scale, 0, 255)
    result[:, :, 2] = np.clip(result[:, :, 2] * b_scale, 0, 255)
    
    logger.debug("화이트밸런스 조정 완료")
    
    return result.astype(np.uint8)


def enhance_contrast(img: np.ndarray) -> np.ndarray:
    """
    대비 향상 (CLAHE: Contrast Limited Adaptive Histogram Equalization)
    
    Args:
        img: 입력 이미지 (numpy 배열)
    
    Returns:
        대비 향상된 이미지
    """
    # RGB 이미지인 경우 LAB 색공간으로 변환
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # L 채널에만 CLAHE 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel_clahe = clahe.apply(l_channel)
        
        # 채널 병합 및 RGB 변환
        lab_clahe = cv2.merge([l_channel_clahe, a_channel, b_channel])
        result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
    else:
        # 그레이스케일인 경우 직접 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        result = clahe.apply(img)
    
    logger.debug("대비 향상 완료")
    
    return result


def remove_noise(img: np.ndarray) -> np.ndarray:
    """
    노이즈 제거 (Non-local Means Denoising)
    
    Args:
        img: 입력 이미지 (numpy 배열)
    
    Returns:
        노이즈 제거된 이미지
    """
    if len(img.shape) == 3:
        # 컬러 이미지
        result = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    else:
        # 그레이스케일 이미지
        result = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    
    logger.debug("노이즈 제거 완료")
    
    return result

