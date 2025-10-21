"""
메인 처리 파이프라인 모듈

PDF 처리의 전체 워크플로우를 오케스트레이션한다.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Callable

from PIL import Image

from app.utils.logger import get_logger
from .rasterize import pdf_to_images, PDFRasterizeError
from .preprocess import auto_enhance
from .pdf import build_searchable_pdf, save_pdf, PDFGenerationError

logger = get_logger("pipeline")


class PipelineError(Exception):
    """파이프라인 처리 관련 예외"""
    pass


class PDFProcessor:
    """
    PDF 처리 파이프라인 클래스
    
    PDF 파일을 입력받아 업스케일, 워터마크 제거, OCR 등의
    처리를 순차적으로 수행한다.
    """
    
    def __init__(
        self,
        options: Optional[Dict] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        """
        Args:
            options: 처리 옵션
                - dpi: PDF 렌더링 DPI (기본값: 300)
                - preprocess: 전처리 옵션
                - upscale: 업스케일 활성화 (기본값: False, Sprint 2에서 구현)
                - watermark: 워터마크 제거 활성화 (기본값: False, Sprint 4에서 구현)
                - ocr: OCR 활성화 (기본값: False, Sprint 3에서 구현)
                - pdfa: PDF/A 표준 준수 (기본값: False)
                - compression: 압축 활성화 (기본값: True)
            progress_callback: 진행률 콜백 함수 (progress: int, message: str)
        """
        self.options = options or {}
        self.progress_callback = progress_callback
        
        # 옵션 기본값 설정
        self.dpi = self.options.get("dpi", 300)
        self.preprocess_options = self.options.get("preprocess", {})
        self.enable_upscale = self.options.get("upscale", False)
        self.enable_watermark = self.options.get("watermark", False)
        self.enable_ocr = self.options.get("ocr", False)
        self.pdfa = self.options.get("pdfa", False)
        self.compression = self.options.get("compression", True)
        
        logger.info(f"파이프라인 초기화: {self.options}")
    
    def process(
        self,
        pdf_path: Union[str, Path, bytes],
        output_path: Union[str, Path],
    ) -> Dict:
        """
        PDF 파일 처리
        
        Args:
            pdf_path: 입력 PDF 파일 경로 또는 바이트 데이터
            output_path: 출력 PDF 파일 경로
        
        Returns:
            처리 결과 딕셔너리
            {
                'success': True/False,
                'output_path': 출력 파일 경로,
                'pages_processed': 처리된 페이지 수,
                'metadata': 메타데이터,
                'error': 에러 메시지 (실패 시)
            }
        
        Raises:
            PipelineError: 처리 실패 시
        """
        try:
            logger.info(f"파이프라인 시작: {pdf_path} → {output_path}")
            
            # 1단계: PDF 래스터화 (10% 진행)
            self._update_progress(10, "PDF를 이미지로 변환 중...")
            images = self._rasterize(pdf_path)
            
            # 2단계: 전처리 (20% 진행)
            self._update_progress(20, "이미지 전처리 중...")
            processed_images = self._preprocess(images)
            
            # 3단계: 업스케일 (옵션, 50% 진행) - Sprint 2에서 구현
            if self.enable_upscale:
                self._update_progress(50, "이미지 업스케일 중...")
                processed_images = self._upscale(processed_images)
            
            # 4단계: 워터마크 제거 (옵션, 65% 진행) - Sprint 4에서 구현
            if self.enable_watermark:
                self._update_progress(65, "워터마크 제거 중...")
                processed_images = self._remove_watermark(processed_images)
            
            # 5단계: OCR (옵션, 80% 진행) - Sprint 3에서 구현
            ocr_results = None
            if self.enable_ocr:
                self._update_progress(80, "OCR 텍스트 인식 중...")
                ocr_results = self._ocr(processed_images)
            
            # 6단계: PDF 생성 (95% 진행)
            self._update_progress(95, "PDF 생성 중...")
            pdf_bytes = self._build_pdf(processed_images, ocr_results)
            
            # 7단계: 파일 저장 (100% 진행)
            self._update_progress(100, "파일 저장 중...")
            save_pdf(pdf_bytes, output_path)
            
            result = {
                "success": True,
                "output_path": str(output_path),
                "pages_processed": len(images),
                "metadata": self._get_metadata(processed_images, ocr_results),
            }
            
            logger.info(f"파이프라인 완료: {result}")
            
            return result
            
        except PDFRasterizeError as e:
            logger.error(f"PDF 래스터화 실패: {e}")
            return {
                "success": False,
                "error": f"PDF 파일 처리 실패: {e}",
                "error_type": "rasterize",
            }
        except PDFGenerationError as e:
            logger.error(f"PDF 생성 실패: {e}")
            return {
                "success": False,
                "error": f"PDF 생성 실패: {e}",
                "error_type": "generation",
            }
        except Exception as e:
            logger.exception(f"파이프라인 처리 중 예상치 못한 오류: {e}")
            return {
                "success": False,
                "error": f"처리 실패: {e}",
                "error_type": "unknown",
            }
    
    def _rasterize(self, pdf_path: Union[str, Path, bytes]) -> List[Image.Image]:
        """PDF를 이미지로 래스터화"""
        return pdf_to_images(pdf_path, dpi=self.dpi)
    
    def _preprocess(self, images: List[Image.Image]) -> List[Image.Image]:
        """이미지 전처리"""
        processed = []
        for idx, img in enumerate(images):
            processed_img = auto_enhance(img, self.preprocess_options)
            processed.append(processed_img)
            logger.debug(f"전처리 완료: 페이지 {idx+1}/{len(images)}")
        return processed
    
    def _upscale(self, images: List[Image.Image]) -> List[Image.Image]:
        """이미지 업스케일"""
        try:
            from .upscale import Upscaler
            
            scale = self.options.get("upscale_scale", 2)
            face_enhance = self.options.get("face_enhance", False)
            
            upscaler = Upscaler(
                scale=scale,
                face_enhance=face_enhance,
            )
            
            results = upscaler.upscale_batch(
                images,
                progress_callback=lambda idx, total: logger.debug(
                    f"업스케일 진행: {idx}/{total}"
                ),
            )
            
            return results
        
        except Exception as e:
            logger.error(f"업스케일 실패, 원본 사용: {e}")
            return images
    
    def _remove_watermark(self, images: List[Image.Image]) -> List[Image.Image]:
        """워터마크 제거 (Sprint 4에서 구현)"""
        logger.warning("워터마크 제거 기능은 Sprint 4에서 구현 예정")
        return images
    
    def _ocr(self, images: List[Image.Image]) -> List[List[dict]]:
        """OCR 텍스트 인식"""
        try:
            from .ocr import OCREngine
            
            engine = self.options.get("ocr_engine", "paddle")
            langs = self.options.get("ocr_langs", "kor+eng")
            use_angle_cls = self.options.get("ocr_use_angle_cls", True)
            min_confidence = self.options.get("ocr_min_confidence", 0.5)
            
            ocr = OCREngine(
                engine=engine,
                langs=langs,
                use_angle_cls=use_angle_cls,
                min_confidence=min_confidence,
            )
            
            results = ocr.recognize_batch(
                images,
                progress_callback=lambda idx, total: logger.debug(
                    f"OCR 진행: {idx}/{total}"
                ),
            )
            
            # 통계 로깅
            stats = ocr.get_statistics(results)
            logger.info(
                f"OCR 완료: {stats['total_texts']}개 텍스트, "
                f"평균 신뢰도 {stats['avg_confidence']:.2f}"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"OCR 실패, 텍스트 레이어 없이 진행: {e}")
            return []
    
    def _build_pdf(
        self,
        images: List[Image.Image],
        ocr_results: Optional[List[List[dict]]],
    ) -> bytes:
        """검색 가능한 PDF 생성"""
        metadata = {
            "title": "Processed PDF",
            "creator": "PDF Upgrade v1.0",
            "producer": "PDF Upgrade Pipeline",
        }
        
        return build_searchable_pdf(
            images,
            ocr_results,
            metadata=metadata,
            pdfa=self.pdfa,
            compression=self.compression,
        )
    
    def _get_metadata(
        self,
        images: List[Image.Image],
        ocr_results: Optional[List[List[dict]]],
    ) -> Dict:
        """처리 메타데이터 생성"""
        return {
            "pages": len(images),
            "dpi": self.dpi,
            "upscale_enabled": self.enable_upscale,
            "watermark_removal_enabled": self.enable_watermark,
            "ocr_enabled": self.enable_ocr,
            "ocr_text_count": sum(len(page) for page in ocr_results) if ocr_results else 0,
        }
    
    def _update_progress(self, progress: int, message: str) -> None:
        """진행률 업데이트"""
        logger.debug(f"진행률: {progress}% - {message}")
        if self.progress_callback:
            try:
                self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"진행률 콜백 실패: {e}")


def process_pdf_simple(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    options: Optional[Dict] = None,
) -> Dict:
    """
    간단한 PDF 처리 함수 (헬퍼)
    
    Args:
        input_path: 입력 PDF 파일 경로
        output_path: 출력 PDF 파일 경로
        options: 처리 옵션
    
    Returns:
        처리 결과 딕셔너리
    """
    processor = PDFProcessor(options)
    return processor.process(input_path, output_path)

