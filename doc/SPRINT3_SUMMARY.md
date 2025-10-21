# Sprint 3 완료 요약

## 📅 기간
2025-10-21

## 🎯 목표
PaddleOCR을 이용한 OCR (광학 문자 인식) 기능 구현

## ✅ 완료된 작업

### 1. OCR 모듈 구현 (`app/pipeline/ocr.py`)

#### 주요 클래스: `OCREngine`
- PaddleOCR / Tesseract 통합
- 한글+영문 동시 인식
- GPU/CPU 자동 선택
- 신뢰도 기반 필터링
- 배치 처리 지원
- 통계 계산

**핵심 기능:**
```python
# 단일 이미지 OCR
ocr = OCREngine(engine="paddle", langs="kor+eng", min_confidence=0.5)
results = ocr.recognize(image)

# 배치 OCR
results = ocr.recognize_batch(images, progress_callback=...)

# 통계 계산
stats = ocr.get_statistics(results)

# 간단한 헬퍼 함수
results = ocr_image_simple(image, engine="paddle", langs="kor+eng")
```

**OCR 결과 형식:**
```python
[
    {
        'text': '인식된 텍스트',
        'bbox': [x, y, width, height],  # 바운딩 박스
        'confidence': 0.95               # 신뢰도 (0-1)
    },
    ...
]
```

**주요 특징:**
- 지연 로딩 (모델은 첫 호출 시 로드)
- 각도 분류기 지원 (회전된 텍스트 인식)
- 신뢰도 임계값 설정
- 진행률 콜백 지원
- 두 가지 엔진 지원 (PaddleOCR, Tesseract)

### 2. 지원 OCR 엔진

#### PaddleOCR (권장)
- **장점**:
  - 한글 인식 정확도 우수
  - 다국어 지원 강력
  - GPU 가속 지원
  - 회전/왜곡 텍스트 처리

- **언어**: korean, en, chinese, japanese 등
- **모델**: PP-OCR v3/v4
- **속도**: 빠름 (GPU 사용 시)

#### Tesseract (대안)
- **장점**:
  - 오래된 검증된 엔진
  - 설치 간단
  - 다양한 언어팩

- **언어**: kor, eng 등
- **버전**: 4.0+
- **속도**: 중간

### 3. 파이프라인 통합

`app/pipeline/pipeline.py`의 `_ocr()` 메서드 구현:
- OCR 모듈 동적 import
- 옵션 기반 설정 (engine, langs, min_confidence)
- 에러 처리 (실패 시 텍스트 레이어 없이 진행)
- 배치 처리 및 진행률 로깅
- 통계 자동 로깅

**파이프라인 흐름:**
```
PDF → 래스터화 → 전처리 → 업스케일 → 워터마크 제거 → [OCR] → PDF 생성
                                                          ↑ Sprint 3
```

**텍스트 레이어 생성:**
- OCR 결과를 PDF 텍스트 레이어로 변환
- 투명 텍스트 (보이지 않음)
- 검색 및 복사 가능
- 좌표 정합 (이미지 픽셀 → PDF 포인트)

### 4. 의존성 추가

`pyproject.toml`에 OCR 의존성 추가:
```toml
[project.optional-dependencies]
ai = [
    "paddleocr>=2.7.0",      # PaddleOCR
    "paddlepaddle>=2.6.0",   # PaddleOCR 의존성 (CPU)
    # GPU: paddlepaddle-gpu 별도 설치
]
```

**설치 방법:**
```bash
# AI 모델 포함 설치
uv sync --extra ai

# GPU 버전 (선택적)
pip install paddlepaddle-gpu
```

### 5. 테스트 스크립트

`examples/test_ocr.py`:
- OCR 기능 간단 테스트
- 테스트 이미지 자동 생성
- 한글+영문 혼합 텍스트
- 결과 출력 및 검증

## 📊 구현 범위

### 구현 완료 ✅
1. PaddleOCR 통합
2. Tesseract 대안 지원
3. 한글+영문 동시 인식
4. GPU/CPU 자동 선택
5. 신뢰도 기반 필터링
6. 각도 분류기 (회전 텍스트)
7. 배치 처리 및 진행률
8. 통계 계산
9. 파이프라인 통합
10. PDF 텍스트 레이어 생성

### 향후 개선 사항 🔜
1. 다국어 확장 (중국어, 일본어)
2. 레이아웃 분석 (표, 문단 구조)
3. OCR 후처리 (맞춤법 교정)
4. 신뢰도별 품질 평가
5. 커스텀 언어 모델

## 🔍 자체 코드 리뷰 결과

### ✅ 잘된 점
1. **엔진 추상화**: PaddleOCR/Tesseract를 동일 인터페이스로 사용
2. **에러 처리**: OCR 실패 시에도 파이프라인 계속 진행
3. **신뢰도 필터**: 낮은 품질 텍스트 자동 제거
4. **통계 제공**: OCR 품질 모니터링 용이
5. **타입 힌팅**: 모든 함수에 타입 힌트
6. **Docstring**: Google 스타일로 상세하게 작성

### ⚠️ 개선 필요 사항
1. **모델 크기**: PaddleOCR 모델이 크므로 다운로드 시간 소요
2. **언어 설정**: Tesseract 경로 수동 설정 필요 (Windows)
3. **좌표 변환**: 이미지 픽셀과 PDF 포인트 정합도 개선 가능
4. **테스트**: 다양한 문서 타입 테스트 필요

**대응 방안:**
- optional-dependencies로 선택 설치 완료
- Tesseract 경로 자동 감지 로직 추가
- PDF 좌표 변환 함수 정교화 (향후)
- 향후 Sprint에서 통합 테스트 추가

## 📈 코드 통계

- **새로 생성된 파일**: 2개
  - `app/pipeline/ocr.py` (약 370줄)
  - `examples/test_ocr.py` (약 60줄)
  
- **수정된 파일**: 2개
  - `app/pipeline/pipeline.py` (_ocr 메서드 구현)
  - `pyproject.toml` (OCR 의존성 추가)

- **총 추가된 코드**: 약 430줄

## 🔧 기술적 결정 사항

### 1. PaddleOCR 선택 (메인)
- **이유**:
  - 한글 인식 정확도가 Tesseract보다 우수
  - 각도 분류기로 회전 텍스트 처리
  - GPU 가속 지원
  - 지속적인 업데이트

### 2. Tesseract 대안 제공
- **이유**:
  - 설치 간단 (일부 환경)
  - 오래된 검증된 엔진
  - 특정 상황에서 유용

### 3. 신뢰도 임계값 (기본 0.5)
- **이유**:
  - 낮은 품질 텍스트 제거
  - PDF 가독성 향상
  - 사용자 정의 가능

### 4. 배치 처리
- **이유**:
  - 여러 페이지 효율적 처리
  - 진행률 추적
  - 에러 격리 (한 페이지 실패해도 계속)

## 🧪 테스트 방법

### 1. 기본 테스트
```python
from app.pipeline.ocr import ocr_image_simple
from PIL import Image

# 이미지 로드
img = Image.open("document.png")

# OCR
results = ocr_image_simple(img, engine="paddle", langs="kor+eng")

# 결과 출력
for item in results:
    print(f"{item['text']} (신뢰도: {item['confidence']:.2f})")
```

### 2. 파이프라인 테스트
```python
from app.pipeline.pipeline import process_pdf_simple

# PDF 처리 (OCR 포함)
result = process_pdf_simple(
    "input.pdf",
    "output.pdf",
    options={
        "ocr": True,
        "ocr_engine": "paddle",
        "ocr_langs": "kor+eng",
        "ocr_min_confidence": 0.5,
    }
)
```

### 3. 통계 확인
```python
from app.pipeline.ocr import OCREngine

ocr = OCREngine(engine="paddle")
results = ocr.recognize_batch(images)
stats = ocr.get_statistics(results)

print(f"총 텍스트: {stats['total_texts']}")
print(f"평균 신뢰도: {stats['avg_confidence']:.2f}")
```

## 🔬 OCR 품질 팁

### 입력 이미지 품질
- **해상도**: 300 DPI 이상 권장
- **대비**: 명확한 배경-텍스트 대비
- **노이즈**: 전처리로 노이즈 제거
- **회전**: 정렬된 텍스트 (또는 각도 분류기 사용)

### 언어 설정
- 한글: `langs="korean"` 또는 `langs="kor"`
- 영문: `langs="en"` 또는 `langs="eng"`
- 혼합: `langs="kor+eng"` (권장)

### 신뢰도 임계값
- 높은 정확도: `min_confidence=0.8`
- 균형: `min_confidence=0.5` (기본)
- 최대 추출: `min_confidence=0.2`

## 🚀 다음 단계

### Sprint 4: 워터마크 제거 기능
- 워터마크 자동 탐지
- 마스크 생성 (U²-Net, 템플릿 매칭)
- LaMa 인페인팅
- 본문 텍스트 보호
- 파이프라인 통합

**예상 작업 범위:**
- `app/pipeline/watermark.py` 구현
- 워터마크 탐지 알고리즘
- 인페인팅 모델 통합
- 품질 평가

## 📝 커밋 기록

### feature/sprint3-ocr 브랜치
1. `feat(sprint3): PaddleOCR 기반 OCR 기능 구현` (예정)
   - OCR 모듈 (PaddleOCR + Tesseract)
   - 한글+영문 동시 인식
   - 신뢰도 필터링
   - 배치 처리
   - 통계 계산
   - 파이프라인 통합
   - OCR 의존성 추가

## 📚 참고 자료

- [PaddleOCR 문서](https://github.com/PaddlePaddle/PaddleOCR)
- [Tesseract 문서](https://github.com/tesseract-ocr/tesseract)
- [PyMuPDF 텍스트 레이어](https://pymupdf.readthedocs.io/)

---

**작성일**: 2025-10-21  
**작성자**: PDF Upgrade Team  
**브랜치**: feature/sprint3-ocr  
**다음 Sprint**: Sprint 4 - 워터마크 제거 기능

