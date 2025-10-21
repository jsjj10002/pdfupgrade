"""
OCR (광학 문자 인식) 모듈

PaddleOCR 또는 Tesseract를 이용한 텍스트 인식
"""

from typing import List, Dict, Optional, Literal
from pathlib import Path

import numpy as np
from PIL import Image

from app.utils.logger import get_logger
from app.utils.device import get_device

logger = get_logger("ocr")


class OCRError(Exception):
    """OCR 관련 예외"""
    pass


class OCREngine:
    """
    OCR 엔진 클래스
    
    PaddleOCR 또는 Tesseract를 사용하여 이미지에서 텍스트를 추출한다.
    """
    
    def __init__(
        self,
        engine: Literal["paddle", "tesseract"] = "paddle",
        langs: str = "kor+eng",
        use_angle_cls: bool = True,
        use_gpu: bool = True,
        min_confidence: float = 0.5,
    ):
        """
        Args:
            engine: OCR 엔진 ('paddle' 또는 'tesseract')
            langs: 인식할 언어 (예: 'kor+eng', 'korean', 'eng')
            use_angle_cls: 각도 분류기 사용 (PaddleOCR)
            use_gpu: GPU 사용 여부
            min_confidence: 최소 신뢰도 임계값
        """
        self.engine = engine
        self.langs = langs
        self.use_angle_cls = use_angle_cls
        self.use_gpu = use_gpu
        self.min_confidence = min_confidence
        
        self.ocr_model = None
        
        logger.info(
            f"OCR 엔진 초기화: engine={engine}, langs={langs}, "
            f"gpu={use_gpu}, min_conf={min_confidence}"
        )
    
    def load_model(self) -> None:
        """
        OCR 모델 로드
        
        처음 호출 시에만 모델을 로드하며, 이후에는 재사용한다.
        """
        if self.ocr_model is not None:
            logger.debug("OCR 모델이 이미 로드되어 있음")
            return
        
        try:
            if self.engine == "paddle":
                self._load_paddle_ocr()
            elif self.engine == "tesseract":
                self._load_tesseract()
            else:
                raise OCRError(f"지원하지 않는 OCR 엔진: {self.engine}")
        
        except Exception as e:
            logger.exception(f"OCR 모델 로드 실패: {e}")
            raise OCRError(f"OCR 모델 로드 실패: {e}") from e
    
    def _load_paddle_ocr(self) -> None:
        """PaddleOCR 모델 로드"""
        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise OCRError(
                "PaddleOCR를 찾을 수 없습니다. "
                "설치: pip install paddleocr"
            ) from e
        
        # 언어 설정
        lang = "korean" if "kor" in self.langs else "en"
        
        # GPU 설정
        use_gpu = self.use_gpu and get_device().type == "cuda"
        
        self.ocr_model = PaddleOCR(
            use_angle_cls=self.use_angle_cls,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False,
            enable_mkldnn=True,  # CPU 가속
            use_tensorrt=False,  # TensorRT 비활성화 (호환성)
        )
        
        logger.info(f"PaddleOCR 모델 로드 완료: lang={lang}, gpu={use_gpu}")
    
    def _load_tesseract(self) -> None:
        """Tesseract OCR 설정"""
        try:
            import pytesseract
        except ImportError as e:
            raise OCRError(
                "pytesseract를 찾을 수 없습니다. "
                "설치: pip install pytesseract\n"
                "Tesseract 바이너리도 설치 필요"
            ) from e
        
        self.ocr_model = pytesseract
        
        # Tesseract 경로 설정 (Windows)
        if Path("C:/Program Files/Tesseract-OCR/tesseract.exe").exists():
            pytesseract.pytesseract.tesseract_cmd = (
                "C:/Program Files/Tesseract-OCR/tesseract.exe"
            )
        
        logger.info(f"Tesseract OCR 설정 완료: langs={self.langs}")
    
    def recognize(self, image: Image.Image) -> List[Dict]:
        """
        이미지에서 텍스트 인식
        
        Args:
            image: 입력 이미지 (PIL Image)
        
        Returns:
            OCR 결과 리스트
            [
                {
                    'text': str,              # 인식된 텍스트
                    'bbox': [x, y, w, h],     # 바운딩 박스
                    'confidence': float,      # 신뢰도 (0-1)
                },
                ...
            ]
        
        Raises:
            OCRError: OCR 실패 시
        """
        # 모델 로드 (최초 1회)
        self.load_model()
        
        try:
            # PIL Image → numpy 배열
            img_np = np.array(image)
            
            logger.debug(f"OCR 시작: {img_np.shape}")
            
            if self.engine == "paddle":
                results = self._recognize_paddle(img_np)
            else:
                results = self._recognize_tesseract(image)
            
            # 신뢰도 필터링
            filtered_results = [
                r for r in results
                if r["confidence"] >= self.min_confidence
            ]
            
            logger.debug(
                f"OCR 완료: {len(results)}개 → "
                f"{len(filtered_results)}개 (min_conf={self.min_confidence})"
            )
            
            return filtered_results
        
        except Exception as e:
            logger.exception(f"OCR 실패: {e}")
            raise OCRError(f"OCR 실패: {e}") from e
    
    def _recognize_paddle(self, img_np: np.ndarray) -> List[Dict]:
        """PaddleOCR로 텍스트 인식"""
        result = self.ocr_model.ocr(img_np, cls=self.use_angle_cls)
        
        if not result or not result[0]:
            return []
        
        ocr_results = []
        
        for line in result[0]:
            # line: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
            box = line[0]
            text, confidence = line[1]
            
            # 바운딩 박스를 [x, y, w, h] 형식으로 변환
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            
            bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
            
            ocr_results.append({
                "text": text,
                "bbox": bbox,
                "confidence": confidence,
            })
        
        return ocr_results
    
    def _recognize_tesseract(self, image: Image.Image) -> List[Dict]:
        """Tesseract로 텍스트 인식"""
        import pytesseract
        
        # 언어 설정 변환 (kor+eng → kor+eng)
        lang = self.langs.replace("+", "+")
        
        # OCR 실행 (상세 데이터)
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )
        
        ocr_results = []
        
        # 각 텍스트 항목 처리
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            if not text:
                continue
            
            confidence = float(data["conf"][i]) / 100.0  # 0-100 → 0-1
            if confidence < 0:
                confidence = 0.0
            
            x = data["left"][i]
            y = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]
            
            ocr_results.append({
                "text": text,
                "bbox": [x, y, w, h],
                "confidence": confidence,
            })
        
        return ocr_results
    
    def recognize_batch(
        self,
        images: List[Image.Image],
        progress_callback: Optional[callable] = None,
    ) -> List[List[Dict]]:
        """
        여러 이미지 배치 OCR
        
        Args:
            images: 입력 이미지 리스트
            progress_callback: 진행률 콜백 함수 (idx, total)
        
        Returns:
            OCR 결과 리스트 (페이지별)
        """
        results = []
        total = len(images)
        
        logger.info(f"배치 OCR 시작: {total}개 이미지")
        
        for idx, img in enumerate(images):
            try:
                result = self.recognize(img)
                results.append(result)
                
                if progress_callback:
                    progress_callback(idx + 1, total)
                
                logger.debug(f"OCR 진행: {idx+1}/{total} ({len(result)}개 텍스트)")
            
            except Exception as e:
                logger.error(f"이미지 {idx+1} OCR 실패: {e}")
                # 실패 시 빈 결과
                results.append([])
        
        logger.info(f"배치 OCR 완료: {len(results)}개 페이지")
        
        return results
    
    def get_statistics(self, ocr_results: List[List[Dict]]) -> Dict:
        """
        OCR 결과 통계 계산
        
        Args:
            ocr_results: OCR 결과 리스트 (페이지별)
        
        Returns:
            통계 딕셔너리
        """
        total_texts = sum(len(page) for page in ocr_results)
        
        if total_texts == 0:
            return {
                "total_pages": len(ocr_results),
                "total_texts": 0,
                "avg_confidence": 0.0,
                "median_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
            }
        
        # 모든 신뢰도 수집
        confidences = []
        for page in ocr_results:
            for item in page:
                confidences.append(item["confidence"])
        
        confidences.sort()
        
        return {
            "total_pages": len(ocr_results),
            "total_texts": total_texts,
            "avg_confidence": sum(confidences) / len(confidences),
            "median_confidence": confidences[len(confidences) // 2],
            "min_confidence": confidences[0],
            "max_confidence": confidences[-1],
        }


def ocr_image_simple(
    image: Image.Image,
    engine: Literal["paddle", "tesseract"] = "paddle",
    langs: str = "kor+eng",
) -> List[Dict]:
    """
    간단한 이미지 OCR 함수 (헬퍼)
    
    Args:
        image: 입력 이미지
        engine: OCR 엔진
        langs: 언어
    
    Returns:
        OCR 결과 리스트
    """
    ocr = OCREngine(engine=engine, langs=langs)
    return ocr.recognize(image)

