"""
PDF 래스터화 모듈

PDF 파일을 페이지별 이미지로 변환한다.
"""

from pathlib import Path
from typing import List, Union

import fitz  # PyMuPDF
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger("rasterize")


class PDFRasterizeError(Exception):
    """PDF 래스터화 관련 예외"""
    pass


def pdf_to_images(
    pdf_path: Union[str, Path, bytes],
    dpi: int = 300,
    start_page: int = 0,
    end_page: int = -1,
) -> List[Image.Image]:
    """
    PDF 파일을 이미지 리스트로 변환
    
    Args:
        pdf_path: PDF 파일 경로 또는 바이트 데이터
        dpi: 렌더링 DPI (기본값: 300)
        start_page: 시작 페이지 인덱스 (0-based)
        end_page: 종료 페이지 인덱스 (-1이면 끝까지)
    
    Returns:
        PIL Image 리스트 (RGB 모드)
    
    Raises:
        PDFRasterizeError: PDF 렌더링 실패 시
    """
    try:
        # PDF 문서 열기
        if isinstance(pdf_path, bytes):
            doc = fitz.open(stream=pdf_path, filetype="pdf")
            logger.debug(f"바이트 스트림에서 PDF 로드 완료 ({len(pdf_path)} bytes)")
        else:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise PDFRasterizeError(f"PDF 파일을 찾을 수 없음: {pdf_path}")
            
            doc = fitz.open(str(pdf_path))
            logger.debug(f"PDF 파일 로드 완료: {pdf_path} ({doc.page_count} 페이지)")
        
        # 페이지 범위 설정
        total_pages = doc.page_count
        if end_page == -1:
            end_page = total_pages
        else:
            end_page = min(end_page, total_pages)
        
        if start_page < 0 or start_page >= total_pages:
            doc.close()
            raise PDFRasterizeError(
                f"잘못된 시작 페이지: {start_page} (전체: {total_pages})"
            )
        
        if end_page <= start_page:
            doc.close()
            raise PDFRasterizeError(
                f"종료 페이지({end_page})가 시작 페이지({start_page})보다 작거나 같음"
            )
        
        logger.info(f"PDF 렌더링 시작: 페이지 {start_page+1}-{end_page}/{total_pages}, DPI={dpi}")
        
        # 페이지별 이미지 변환
        images = []
        zoom = dpi / 72.0  # 72 DPI가 기본값
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(start_page, end_page):
            try:
                page = doc[page_num]
                
                # 페이지를 픽셀맵으로 렌더링 (RGB, alpha 없음)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                # PIL Image로 변환
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                
                # RGB 모드로 변환 (일부 PDF는 다른 모드일 수 있음)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                images.append(img)
                
                logger.debug(
                    f"페이지 {page_num+1}/{end_page} 렌더링 완료 "
                    f"({img.width}x{img.height})"
                )
                
            except Exception as e:
                logger.error(f"페이지 {page_num+1} 렌더링 실패: {e}")
                # 페이지 렌더링 실패 시 빈 이미지 또는 예외 발생
                # 여기서는 예외를 발생시켜 전체 처리를 중단
                doc.close()
                raise PDFRasterizeError(
                    f"페이지 {page_num+1} 렌더링 실패: {e}"
                ) from e
        
        doc.close()
        logger.info(f"PDF 렌더링 완료: {len(images)}개 페이지")
        
        return images
        
    except fitz.FileDataError as e:
        logger.error(f"손상된 PDF 파일: {e}")
        raise PDFRasterizeError(f"손상된 PDF 파일: {e}") from e
    except fitz.FileNotFoundError as e:
        logger.error(f"PDF 파일을 찾을 수 없음: {e}")
        raise PDFRasterizeError(f"PDF 파일을 찾을 수 없음: {e}") from e
    except Exception as e:
        logger.exception(f"PDF 렌더링 중 예상치 못한 오류: {e}")
        raise PDFRasterizeError(f"PDF 렌더링 실패: {e}") from e


def get_pdf_info(pdf_path: Union[str, Path, bytes]) -> dict:
    """
    PDF 파일 정보 추출
    
    Args:
        pdf_path: PDF 파일 경로 또는 바이트 데이터
    
    Returns:
        PDF 정보 딕셔너리
        {
            'page_count': 페이지 수,
            'title': 제목,
            'author': 저자,
            'subject': 주제,
            'creator': 생성 프로그램,
            'producer': PDF 생성기,
            'creation_date': 생성 날짜,
            'modification_date': 수정 날짜,
            'format': PDF 형식 (예: 'PDF 1.7'),
            'encrypted': 암호화 여부,
        }
    
    Raises:
        PDFRasterizeError: PDF 정보 추출 실패 시
    """
    try:
        if isinstance(pdf_path, bytes):
            doc = fitz.open(stream=pdf_path, filetype="pdf")
        else:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise PDFRasterizeError(f"PDF 파일을 찾을 수 없음: {pdf_path}")
            doc = fitz.open(str(pdf_path))
        
        metadata = doc.metadata
        info = {
            "page_count": doc.page_count,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "format": metadata.get("format", ""),
            "encrypted": doc.is_encrypted,
        }
        
        doc.close()
        return info
        
    except Exception as e:
        logger.exception(f"PDF 정보 추출 실패: {e}")
        raise PDFRasterizeError(f"PDF 정보 추출 실패: {e}") from e


# io 모듈 import 추가 (이미지 변환에 필요)
import io

