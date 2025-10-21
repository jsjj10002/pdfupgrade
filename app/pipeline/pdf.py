"""
PDF 생성 모듈

처리된 이미지로 검색 가능한 PDF를 생성한다.
"""

import io
from pathlib import Path
from typing import List, Optional, Union

import fitz  # PyMuPDF
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger("pdf")


class PDFGenerationError(Exception):
    """PDF 생성 관련 예외"""
    pass


def build_searchable_pdf(
    images: List[Image.Image],
    ocr_results: Optional[List[List[dict]]] = None,
    metadata: Optional[dict] = None,
    pdfa: bool = False,
    compression: bool = True,
) -> bytes:
    """
    이미지와 OCR 결과로 검색 가능한 PDF 생성
    
    Args:
        images: PIL Image 리스트 (페이지별)
        ocr_results: OCR 결과 리스트 (페이지별)
            각 페이지는 [{'text': str, 'bbox': [x, y, w, h], 'confidence': float}, ...] 형식
        metadata: PDF 메타데이터 딕셔너리
        pdfa: PDF/A 표준 준수 여부
        compression: 이미지 압축 활성화
    
    Returns:
        PDF 파일 바이트 데이터
    
    Raises:
        PDFGenerationError: PDF 생성 실패 시
    """
    try:
        # 새 PDF 문서 생성
        doc = fitz.open()
        
        logger.info(f"PDF 생성 시작: {len(images)}개 페이지")
        
        for page_idx, img in enumerate(images):
            # 이미지를 PNG 바이트로 변환
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG", optimize=compression)
            img_data = img_bytes.getvalue()
            
            # 새 페이지 생성 (이미지 크기에 맞춤)
            page = doc.new_page(width=img.width, height=img.height)
            
            # 페이지에 이미지 삽입
            rect = fitz.Rect(0, 0, img.width, img.height)
            page.insert_image(rect, stream=img_data)
            
            # OCR 텍스트 레이어 추가 (있는 경우)
            if ocr_results and page_idx < len(ocr_results):
                page_ocr = ocr_results[page_idx]
                insert_text_layer(page, page_ocr, img.width, img.height)
            
            logger.debug(f"페이지 {page_idx+1}/{len(images)} 추가 완료")
        
        # 메타데이터 설정
        if metadata:
            doc.set_metadata(metadata)
            logger.debug(f"메타데이터 설정: {metadata}")
        
        # PDF/A 표준 준수 (향후 구현)
        if pdfa:
            logger.warning("PDF/A 표준은 아직 구현되지 않았습니다")
        
        # PDF 바이트 생성
        pdf_bytes = doc.tobytes(
            deflate=compression,
            garbage=4,  # 가비지 컬렉션 레벨
            clean=True,
        )
        
        doc.close()
        
        logger.info(f"PDF 생성 완료: {len(pdf_bytes)} bytes")
        
        return pdf_bytes
        
    except Exception as e:
        logger.exception(f"PDF 생성 실패: {e}")
        raise PDFGenerationError(f"PDF 생성 실패: {e}") from e


def insert_text_layer(
    page: fitz.Page,
    ocr_result: List[dict],
    page_width: int,
    page_height: int,
) -> None:
    """
    PDF 페이지에 OCR 텍스트 레이어 삽입
    
    텍스트는 보이지 않지만 검색/복사 가능하도록 설정
    
    Args:
        page: PyMuPDF 페이지 객체
        ocr_result: OCR 결과 리스트 [{'text', 'bbox', 'confidence'}, ...]
        page_width: 페이지 너비
        page_height: 페이지 높이
    """
    try:
        for item in ocr_result:
            text = item.get("text", "").strip()
            if not text:
                continue
            
            bbox = item.get("bbox", [0, 0, 100, 100])
            confidence = item.get("confidence", 0.0)
            
            # 신뢰도가 낮은 텍스트는 제외
            if confidence < 0.5:
                continue
            
            # bbox를 PDF 좌표계로 변환
            # OCR bbox: [x, y, w, h] (픽셀 좌표)
            # PDF rect: (x0, y0, x1, y1) (PDF 포인트)
            x, y, w, h = bbox
            
            # 픽셀 → PDF 포인트 변환 (72 DPI 기준)
            # 실제로는 페이지 크기가 이미지 픽셀과 동일하므로 그대로 사용
            rect = fitz.Rect(x, y, x + w, y + h)
            
            # 텍스트 삽입 (투명, 보이지 않음)
            try:
                page.insert_textbox(
                    rect,
                    text,
                    fontname="helv",  # Helvetica
                    fontsize=h * 0.8,  # 박스 높이의 80%
                    color=(0, 0, 0),  # 검은색 (하지만 투명하게 설정)
                    fill_opacity=0.0,  # 완전 투명
                    stroke_opacity=0.0,  # 테두리 투명
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            except Exception as e:
                # 텍스트 삽입 실패 시 로그만 기록하고 계속 진행
                logger.debug(f"텍스트 삽입 실패 ('{text[:20]}...'): {e}")
        
        logger.debug(f"텍스트 레이어 삽입 완료: {len(ocr_result)}개 항목")
        
    except Exception as e:
        logger.warning(f"텍스트 레이어 삽입 중 오류: {e}")


def save_pdf(
    pdf_bytes: bytes,
    output_path: Union[str, Path],
) -> None:
    """
    PDF 바이트 데이터를 파일로 저장
    
    Args:
        pdf_bytes: PDF 파일 바이트 데이터
        output_path: 저장할 파일 경로
    
    Raises:
        PDFGenerationError: 파일 저장 실패 시
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        
        logger.info(f"PDF 파일 저장 완료: {output_path} ({len(pdf_bytes)} bytes)")
        
    except Exception as e:
        logger.exception(f"PDF 파일 저장 실패: {e}")
        raise PDFGenerationError(f"PDF 파일 저장 실패: {e}") from e


def merge_pdfs(
    pdf_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
) -> None:
    """
    여러 PDF 파일을 하나로 병합
    
    Args:
        pdf_paths: 병합할 PDF 파일 경로 리스트
        output_path: 결과 PDF 파일 경로
    
    Raises:
        PDFGenerationError: PDF 병합 실패 시
    """
    try:
        result_doc = fitz.open()
        
        for pdf_path in pdf_paths:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.warning(f"파일을 찾을 수 없어 건너뜀: {pdf_path}")
                continue
            
            doc = fitz.open(str(pdf_path))
            result_doc.insert_pdf(doc)
            doc.close()
            
            logger.debug(f"PDF 병합: {pdf_path}")
        
        result_doc.save(str(output_path))
        result_doc.close()
        
        logger.info(f"PDF 병합 완료: {len(pdf_paths)}개 파일 → {output_path}")
        
    except Exception as e:
        logger.exception(f"PDF 병합 실패: {e}")
        raise PDFGenerationError(f"PDF 병합 실패: {e}") from e

