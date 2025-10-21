# Sprint 4 완료 요약

## 📅 기간
2025-10-21

## 🎯 목표
워터마크 자동 탐지 및 제거 기능 구현

## ✅ 완료된 작업

### 1. 워터마크 제거 모듈 구현 (`app/pipeline/watermark.py`)

#### 주요 클래스: `WatermarkRemover`
- 워터마크 자동 탐지
- 다중 탐지 알고리즘
- OpenCV 인페인팅
- 본문 텍스트 보호
- 배치 처리 지원

**핵심 기능:**
```python
# 단일 이미지 워터마크 제거
remover = WatermarkRemover(method="auto", protect_text=True)
result = remover.remove(image)

# 커스텀 마스크 사용
result = remover.remove(image, mask=custom_mask)

# 배치 제거
results = remover.remove_batch(images, progress_callback=...)

# 간단한 헬퍼 함수
result = remove_watermark_simple(image, method="auto")
```

**지원하는 제거 방법:**
- `auto`: 자동 선택 (권장)
- `opencv`: OpenCV 인페인팅 (빠름)
- `template`: 템플릿 매칭 (반복 패턴)
- `lama`: LaMa 인페인팅 (향후 구현)

### 2. 워터마크 탐지 알고리즘

#### 다중 탐지 방법 조합
1. **반투명 영역 탐지**
   - HSV 색공간 분석
   - 낮은 채도 + 중간~높은 명도 영역
   - 워터마크의 반투명 특성 활용

2. **색상 이상 영역 탐지**
   - 적응형 임계값
   - 엣지 검출 (Canny)
   - 본문과 다른 색상 패턴

3. **고주파 패턴 탐지**
   - FFT(Fast Fourier Transform)
   - 주파수 도메인 분석
   - 반복 로고/텍스트 패턴

**마스크 통합:**
```python
# 3가지 방법의 결과를 OR 연산으로 통합
combined_mask = max(mask_alpha, mask_color, mask_pattern)

# 모폴로지 연산으로 노이즈 제거
mask = morphologyEx(combined_mask, MORPH_CLOSE)
mask = morphologyEx(mask, MORPH_OPEN)
```

### 3. 본문 텍스트 보호

#### MSER(Maximally Stable Extremal Regions) 활용
- 본문 텍스트 영역 자동 탐지
- 워터마크 마스크에서 텍스트 제외
- 안전 마진 적용 (dilation)

**보호 프로세스:**
```
1. MSER로 텍스트 후보 영역 탐지
2. 작은 영역만 텍스트로 분류
3. 텍스트 영역 확장 (안전 마진)
4. 워터마크 마스크에서 제외
5. 최종 마스크 반환
```

### 4. 인페인팅 (복원)

#### OpenCV 인페인팅 (구현 완료)
- **Telea 알고리즘**: 빠르고 효과적
- **처리 속도**: 빠름 (실시간 가능)
- **품질**: 중~상
- **용도**: 작은~중간 크기 워터마크

#### LaMa 인페인팅 (향후)
- **딥러닝 기반**: 고품질 복원
- **처리 속도**: 느림
- **품질**: 최고
- **용도**: 큰 워터마크, 복잡한 배경

### 5. 파이프라인 통합

`app/pipeline/pipeline.py`의 `_remove_watermark()` 메서드 구현:
- 워터마크 모듈 동적 import
- 옵션 기반 설정 (method, threshold, protect_text)
- 에러 처리 (실패 시 원본 사용)
- 배치 처리 및 진행률 로깅

**완전한 파이프라인:**
```
PDF → 래스터화 → 전처리 → 업스케일 → [워터마크 제거] → OCR → PDF 생성
                                          ↑ Sprint 4
```

### 6. 테스트 스크립트

`examples/test_watermark.py`:
- 워터마크 있는 테스트 이미지 자동 생성
- 반투명 대각선 워터마크
- 제거 전후 비교
- 결과 이미지 저장

## 📊 구현 범위

### 구현 완료 ✅
1. 워터마크 자동 탐지 (3가지 알고리즘)
2. 마스크 생성 및 정제
3. 본문 텍스트 보호 (MSER)
4. OpenCV 인페인팅
5. 배치 처리 및 진행률
6. 파이프라인 통합
7. 에러 처리

### 향후 개선 사항 🔜
1. LaMa 인페인팅 통합
2. 딥러닝 기반 워터마크 탐지 (U²-Net, SAM)
3. 템플릿 매칭 기반 탐지 (반복 패턴)
4. 워터마크 유형별 특화 알고리즘
5. 품질 평가 메트릭

## 🔍 자체 코드 리뷰 결과

### ✅ 잘된 점
1. **다중 탐지 방법**: 다양한 워터마크 유형에 대응
2. **텍스트 보호**: 본문 손상 방지
3. **에러 처리**: 실패 시에도 파이프라인 계속
4. **배치 처리**: 여러 페이지 효율적 처리
5. **타입 힌팅**: 모든 함수에 타입 힌트
6. **Docstring**: Google 스타일로 상세하게 작성

### ⚠️ 개선 필요 사항
1. **탐지 정확도**: 복잡한 워터마크는 오탐/미탐 가능
2. **LaMa 미구현**: 고품질 인페인팅은 향후 추가
3. **템플릿 매칭**: 반복 패턴 워터마크 특화 미구현
4. **성능**: FFT 연산은 상대적으로 느림

**대응 방안:**
- 다중 알고리즘으로 탐지율 향상
- OpenCV 인페인팅으로 실용적 품질 확보
- LaMa는 선택적 기능으로 향후 추가
- 향후 딥러닝 기반 탐지로 정확도 개선

## 📈 코드 통계

- **새로 생성된 파일**: 2개
  - `app/pipeline/watermark.py` (약 380줄)
  - `examples/test_watermark.py` (약 70줄)
  
- **수정된 파일**: 1개
  - `app/pipeline/pipeline.py` (_remove_watermark 메서드 구현)

- **총 추가된 코드**: 약 450줄

## 🔧 기술적 결정 사항

### 1. 다중 탐지 알고리즘
- **이유**:
  - 워터마크 유형이 다양함
  - 단일 방법으로는 한계
  - OR 연산으로 통합하여 커버리지 향상

### 2. OpenCV 인페인팅 우선
- **이유**:
  - 빠른 처리 속도
  - 외부 의존성 없음
  - 실용적인 품질
  - LaMa는 선택적 추가

### 3. MSER 기반 텍스트 보호
- **이유**:
  - 딥러닝 없이 효과적
  - 빠른 처리
  - 다양한 폰트/크기 대응

### 4. 모폴로지 연산
- **이유**:
  - 마스크 노이즈 제거
  - 연결성 개선
  - 간단하고 효과적

## 🧪 테스트 방법

### 1. 기본 테스트
```python
from app.pipeline.watermark import remove_watermark_simple
from PIL import Image

# 이미지 로드
img = Image.open("watermarked.png")

# 워터마크 제거
result = remove_watermark_simple(img, method="auto")
result.save("clean.png")
```

### 2. 파이프라인 테스트
```python
from app.pipeline.pipeline import process_pdf_simple

# PDF 처리 (워터마크 제거 포함)
result = process_pdf_simple(
    "input.pdf",
    "output.pdf",
    options={
        "watermark": True,
        "watermark_method": "auto",
        "watermark_threshold": 0.8,
        "watermark_protect_text": True,
    }
)
```

### 3. 커스텀 마스크 테스트
```python
from app.pipeline.watermark import WatermarkRemover
import numpy as np

# 커스텀 마스크 생성
mask = np.zeros((600, 800), dtype=np.uint8)
mask[200:400, 300:500] = 255  # 워터마크 영역

# 제거
remover = WatermarkRemover(method="opencv")
result = remover.remove(image, mask=mask)
```

## 🎯 워터마크 제거 팁

### 입력 이미지 품질
- **해상도**: 높을수록 탐지 정확도 향상
- **대비**: 명확한 워터마크일수록 탐지 용이
- **위치**: 반복 패턴 워터마크는 탐지 쉬움

### 방법 선택
- `auto`: 대부분의 경우 권장
- `opencv`: 빠른 처리 필요 시
- `template`: 반복 패턴 워터마크 (향후)

### 임계값 조정
- 높은 정확도: `detection_threshold=0.9`
- 균형: `detection_threshold=0.8` (기본)
- 최대 탐지: `detection_threshold=0.6`

### 텍스트 보호
- 문서: `protect_text=True` (권장)
- 단순 이미지: `protect_text=False`

## 🚀 다음 단계

### Sprint 5: FastAPI 서버 및 작업 큐
- FastAPI REST API 엔드포인트
- 파일 업로드/다운로드
- Celery 작업 큐 (Redis)
- WebSocket 진행률 스트리밍
- 작업 상태 관리
- 에러 핸들링

**예상 작업 범위:**
- `app/api/main.py` - FastAPI 앱
- `app/api/routes/` - 엔드포인트
- `app/api/schemas.py` - Pydantic 스키마
- `app/workers/celery_app.py` - Celery 설정
- `app/workers/tasks.py` - 태스크 정의

## 📝 커밋 기록

### feature/sprint4-watermark 브랜치
1. `feat(sprint4): 워터마크 자동 탐지 및 제거 기능 구현` (예정)
   - 워터마크 제거 모듈
   - 다중 탐지 알고리즘 (반투명, 색상, 고주파)
   - 본문 텍스트 보호 (MSER)
   - OpenCV 인페인팅
   - 배치 처리
   - 파이프라인 통합

## 📚 참고 자료

- [OpenCV Inpainting](https://docs.opencv.org/4.x/df/d3d/tutorial_py_inpainting.html)
- [LaMa (Large Mask Inpainting)](https://github.com/advimman/lama)
- [MSER Text Detection](https://docs.opencv.org/4.x/d3/d28/classcv_1_1MSER.html)

## 🎊 Sprint 4 완료!

**모든 이미지 처리 기능이 완성되었다!**

이제 PDF 처리 파이프라인의 **핵심 기능**이 100% 완성:
- ✅ 래스터화
- ✅ 전처리
- ✅ 업스케일
- ✅ 워터마크 제거
- ✅ OCR

남은 작업은 **사용자 인터페이스**:
- 🔜 FastAPI 서버 (REST API)
- 🔜 Celery 작업 큐 (비동기 처리)
- 🔜 React 프론트엔드 (UI)
- 🔜 Docker 배포 (프로덕션)

---

**작성일**: 2025-10-21  
**작성자**: PDF Upgrade Team  
**브랜치**: feature/sprint4-watermark  
**다음 Sprint**: Sprint 5 - FastAPI 서버 및 작업 큐

