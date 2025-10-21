# PDF Upgrade - 프로젝트 청사진

## 목차
- [1. 핵심 아키텍처](#1-핵심-아키텍처)
- [2. 컴포넌트/모듈 명세서](#2-컴포넌트모듈-명세서)
- [3. 주요 로직 흐름](#3-주요-로직-흐름)
- [4. API 명세서](#4-api-명세서)

---

## 1. 핵심 아키텍처

### 1.1 시스템 개요
PDF Upgrade는 AI 기반 PDF 품질 개선 플랫폼으로, 이미지 품질이 낮거나 워터마크가 포함된 PDF 파일을 고품질의 검색 가능한 PDF로 변환한다.

### 1.2 기술 스택

#### 백엔드
- **언어**: Python 3.11+
- **웹 프레임워크**: FastAPI
- **비동기 작업 큐**: Celery + Redis
- **딥러닝 프레임워크**: PyTorch (CUDA 지원)
- **PDF 처리**: PyMuPDF (fitz), pikepdf
- **이미지 처리**: Pillow, OpenCV

#### AI/ML 모델
- **업스케일**: Real-ESRGAN (x2, x4)
- **얼굴 보정**: GFPGAN (선택적)
- **워터마크 제거**: LaMa 인페인팅 또는 U²-Net + 인페인팅
- **OCR**: PaddleOCR (한글+영문) 또는 Tesseract

#### 프론트엔드
- **프레임워크**: React 18
- **언어**: TypeScript
- **빌드 도구**: Vite
- **스타일링**: TailwindCSS
- **UI 라이브러리**: Headless UI, Radix UI

#### 인프라
- **컨테이너화**: Docker, Docker Compose
- **GPU 지원**: NVIDIA Container Toolkit
- **메시지 브로커/캐시**: Redis 7
- **스토리지**: 로컬 파일시스템 (개발), S3 호환 스토리지 (운영)

### 1.3 시스템 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
│                    React + TypeScript + Vite                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Server                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │   Upload     │  │   Job Mgmt   │  │   Download        │     │
│  │   Endpoint   │  │   Endpoint   │  │   Endpoint        │     │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────────┘     │
│         │                  │                   │                  │
└─────────┼──────────────────┼───────────────────┼─────────────────┘
          │                  │                   │
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Redis Queue                              │
│                    (Celery Message Broker)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Celery Workers                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Processing Pipeline                         │    │
│  │                                                          │    │
│  │  PDF → Rasterize → Preprocess → Upscale → Watermark    │    │
│  │        → OCR → Build Searchable PDF → Storage           │    │
│  │                                                          │    │
│  │  Modules:                                                │    │
│  │  - rasterize.py: PDF to images                          │    │
│  │  - preprocess.py: 이미지 전처리                          │    │
│  │  - upscale.py: Real-ESRGAN 업스케일                     │    │
│  │  - watermark.py: 워터마크 제거                           │    │
│  │  - ocr.py: PaddleOCR 텍스트 인식                        │    │
│  │  - pdf.py: 검색 가능한 PDF 생성                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      File Storage                                │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐                  │
│   │   Input   │  │   Temp    │  │   Output  │                  │
│   └───────────┘  └───────────┘  └───────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 배포 구조

```
┌──────────────────────────────────────────────────────────┐
│                     Docker Host                          │
│                                                          │
│  ┌─────────────────┐  ┌────────────────┐               │
│  │  FastAPI        │  │  Celery Worker │               │
│  │  Container      │  │  Container     │               │
│  │  (Port 8000)    │  │  (GPU Access)  │               │
│  └────────┬────────┘  └────────┬───────┘               │
│           │                     │                        │
│           └──────────┬──────────┘                        │
│                      │                                   │
│           ┌──────────▼──────────┐                        │
│           │   Redis Container   │                        │
│           │   (Port 6379)       │                        │
│           └─────────────────────┘                        │
│                                                          │
│  Volume Mounts:                                          │
│  - ./storage:/app/storage                                │
│  - ./models:/app/models                                  │
│  - ./logs:/app/logs                                      │
└──────────────────────────────────────────────────────────┘
```

### 1.5 데이터 흐름

1. **업로드**: 클라이언트가 PDF 파일과 옵션을 API 서버로 전송
2. **작업 생성**: API 서버가 파일을 저장하고 Celery 작업 생성
3. **큐 등록**: Redis 큐에 작업 ID와 매개변수 등록
4. **워커 처리**: Celery 워커가 작업을 가져와 파이프라인 실행
5. **진행률 업데이트**: 각 단계마다 Redis에 진행 상태 저장
6. **결과 저장**: 처리된 PDF를 스토리지에 저장
7. **완료 알림**: WebSocket을 통해 클라이언트에 완료 알림
8. **다운로드**: 클라이언트가 결과 파일 다운로드

---

## 2. 컴포넌트/모듈 명세서

### 2.1 백엔드 모듈

#### 2.1.1 API 모듈 (`app/api/`)

##### `main.py`
- **역할**: FastAPI 애플리케이션 진입점
- **책임**:
  - CORS 설정
  - 미들웨어 등록
  - 라우터 등록
  - 예외 핸들러 설정

##### `routes/jobs.py`
- **역할**: 작업 관리 엔드포인트
- **책임**:
  - 파일 업로드 처리
  - 작업 생성 및 큐 등록
  - 작업 상태 조회
  - 결과 파일 다운로드

##### `routes/health.py`
- **역할**: 헬스 체크 엔드포인트
- **책임**:
  - API 서버 상태 확인
  - Redis 연결 상태 확인
  - GPU 가용성 확인

##### `schemas.py`
- **역할**: Pydantic 스키마 정의
- **책임**:
  - 요청/응답 데이터 모델
  - 유효성 검증 규칙

##### `dependencies.py`
- **역할**: FastAPI 의존성 주입
- **책임**:
  - Redis 클라이언트 제공
  - 설정 객체 제공

#### 2.1.2 파이프라인 모듈 (`app/pipeline/`)

##### `pipeline.py`
- **역할**: 메인 처리 파이프라인 오케스트레이션
- **책임**:
  - 각 처리 단계 순차 실행
  - 에러 핸들링 및 복구
  - 진행률 추적
  - 리소스 정리

##### `rasterize.py`
- **역할**: PDF를 이미지로 변환
- **책임**:
  - PyMuPDF를 이용한 페이지 렌더링
  - DPI 설정 및 해상도 조정
  - 메모리 효율적 처리

##### `preprocess.py`
- **역할**: 이미지 전처리
- **책임**:
  - 자동 회전 및 디스큐
  - 화이트밸런스 조정
  - 노이즈 제거
  - 대비 향상 (CLAHE)

##### `upscale.py`
- **역할**: 이미지 해상도 향상
- **책임**:
  - Real-ESRGAN 모델 로드 및 추론
  - GPU/CPU 자동 선택
  - 배치 처리 최적화
  - GFPGAN 얼굴 보정 (선택적)

##### `watermark.py`
- **역할**: 워터마크 탐지 및 제거
- **책임**:
  - 워터마크 영역 자동 탐지
  - 마스크 생성 (U²-Net 또는 템플릿 매칭)
  - LaMa 인페인팅 적용
  - 본문 텍스트 보호

##### `ocr.py`
- **역할**: 광학 문자 인식
- **책임**:
  - PaddleOCR/Tesseract 엔진 관리
  - 텍스트 및 좌표 추출
  - 신뢰도 점수 계산
  - 다국어 지원

##### `pdf.py`
- **역할**: 검색 가능한 PDF 생성
- **책임**:
  - 처리된 이미지로 PDF 재구성
  - OCR 텍스트 레이어 삽입
  - 메타데이터 설정
  - PDF/A 표준 준수 (선택적)

#### 2.1.3 워커 모듈 (`app/workers/`)

##### `celery_app.py`
- **역할**: Celery 애플리케이션 설정
- **책임**:
  - Celery 인스턴스 생성
  - Redis 브로커 연결
  - 워커 설정 (동시성, 타임아웃)

##### `tasks.py`
- **역할**: Celery 태스크 정의
- **책임**:
  - `process_pdf` 태스크 구현
  - 진행률 업데이트
  - 에러 복구 및 재시도
  - 결과 저장

#### 2.1.4 유틸리티 모듈 (`app/utils/`)

##### `config.py`
- **역할**: 환경 변수 및 설정 관리
- **책임**:
  - .env 파일 로드
  - Pydantic Settings 스키마
  - 필수 설정 검증
  - 기본값 제공

##### `device.py`
- **역할**: GPU/CPU 장치 관리
- **책임**:
  - CUDA 가용성 확인
  - nvidia-smi 실행 검증
  - 최적 장치 선택
  - 메모리 모니터링

##### `logger.py`
- **역할**: 로깅 설정
- **책임**:
  - 구조화된 로그 포맷
  - 로그 레벨 관리
  - 파일 및 콘솔 출력
  - 로그 로테이션

##### `storage.py`
- **역할**: 파일 저장소 관리
- **책임**:
  - 파일 저장/로드/삭제
  - 경로 생성 및 정리
  - 임시 파일 관리
  - S3 호환 스토리지 지원 (향후)

##### `validators.py`
- **역할**: 입력 검증
- **책임**:
  - 파일 크기 제한
  - MIME 타입 검증
  - PDF 유효성 검사
  - 파일명 sanitization

#### 2.1.5 모델 모듈 (`app/models/`)

##### `model_manager.py`
- **역할**: AI 모델 관리
- **책임**:
  - 모델 가중치 다운로드
  - 모델 캐싱 및 프리로드
  - 버전 관리
  - 메모리 효율적 로드

### 2.2 프론트엔드 컴포넌트 (`frontend/src/`)

#### 2.2.1 페이지 컴포넌트

##### `pages/UploadPage.tsx`
- **역할**: 메인 업로드 페이지
- **책임**:
  - 파일 선택 UI
  - 옵션 체크박스 (업스케일, 워터마크, OCR)
  - 드래그 앤 드롭
  - 파일 미리보기

##### `pages/ProcessingPage.tsx`
- **역할**: 처리 진행 상황 페이지
- **책임**:
  - 진행률 표시
  - 단계별 상태 표시
  - 취소 기능
  - 에러 표시

##### `pages/ResultPage.tsx`
- **역할**: 결과 페이지
- **책임**:
  - 처리 결과 요약
  - 다운로드 버튼
  - 새 작업 시작 버튼

#### 2.2.2 공통 컴포넌트

##### `components/FileUploader.tsx`
- **역할**: 파일 업로드 컴포넌트
- **책임**:
  - 다중 파일 선택
  - 드래그 앤 드롭
  - 파일 목록 표시
  - 파일 제거

##### `components/OptionSelector.tsx`
- **역할**: 처리 옵션 선택
- **책임**:
  - 업스케일 배율 선택
  - 워터마크 제거 모드
  - OCR 언어 선택
  - 고급 옵션 토글

##### `components/ProgressBar.tsx`
- **역할**: 진행률 표시
- **책임**:
  - 퍼센트 표시
  - 단계별 상태
  - 애니메이션

##### `components/ErrorBoundary.tsx`
- **역할**: 에러 처리
- **책임**:
  - 에러 캐치
  - 사용자 친화적 에러 메시지
  - 복구 옵션

#### 2.2.3 서비스

##### `services/api.ts`
- **역할**: API 클라이언트
- **책임**:
  - HTTP 요청 래퍼
  - 에러 처리
  - 인터셉터
  - 타임아웃 관리

##### `services/websocket.ts`
- **역할**: WebSocket 연결 관리
- **책임**:
  - 실시간 진행률 수신
  - 재연결 로직
  - 이벤트 핸들링

---

## 3. 주요 로직 흐름

### 3.1 PDF 처리 플로우

#### 3.1.1 전체 플로우 (End-to-End)

```
[클라이언트]
    │
    ├─ 1. 파일 선택 + 옵션 선택
    │   ├─ 업스케일 활성화 (배율: x2 또는 x4)
    │   ├─ 워터마크 제거 활성화
    │   └─ OCR 활성화 (언어: 한글+영문)
    │
    ├─ 2. POST /api/jobs (multipart/form-data)
    │   ├─ files[]: PDF 파일들
    │   └─ options: JSON (upscale, watermark, ocr, scale, langs)
    │
    ▼
[API 서버]
    │
    ├─ 3. 파일 검증
    │   ├─ MIME 타입 확인 (application/pdf)
    │   ├─ 파일 크기 확인 (< 250MB)
    │   └─ PDF 유효성 검사
    │
    ├─ 4. 파일 저장
    │   └─ storage/input/{job_id}/{filename}.pdf
    │
    ├─ 5. Celery 태스크 생성
    │   └─ task_id = process_pdf.delay(job_id, file_paths, options)
    │
    ├─ 6. 응답 반환
    │   └─ {"job_id": "...", "task_id": "...", "status": "queued"}
    │
    ▼
[Celery Worker]
    │
    ├─ 7. 태스크 시작
    │   └─ 상태 업데이트: "queued" → "processing"
    │
    ├─ 8. 파이프라인 실행 (각 PDF 파일에 대해)
    │   │
    │   ├─ 8.1 PDF 래스터화 (10% 진행)
    │   │   ├─ PyMuPDF로 페이지별 렌더링 (DPI 300)
    │   │   └─ PIL Image 리스트 생성
    │   │
    │   ├─ 8.2 전처리 (20% 진행)
    │   │   ├─ 이미지 회전 보정
    │   │   ├─ 화이트밸런스 조정
    │   │   └─ 노이즈 제거
    │   │
    │   ├─ 8.3 업스케일 (옵션, 50% 진행)
    │   │   ├─ Real-ESRGAN 모델 로드 (GPU)
    │   │   ├─ 페이지별 업스케일 추론
    │   │   └─ 결과 이미지 저장
    │   │
    │   ├─ 8.4 워터마크 제거 (옵션, 65% 진행)
    │   │   ├─ 워터마크 영역 탐지 (템플릿 매칭 또는 U²-Net)
    │   │   ├─ 마스크 생성
    │   │   └─ LaMa 인페인팅 적용
    │   │
    │   ├─ 8.5 OCR (옵션, 80% 진행)
    │   │   ├─ PaddleOCR 실행 (한글+영문)
    │   │   ├─ 텍스트 및 좌표 추출
    │   │   └─ 신뢰도 점수 계산
    │   │
    │   ├─ 8.6 PDF 생성 (95% 진행)
    │   │   ├─ 처리된 이미지로 새 PDF 생성
    │   │   ├─ OCR 텍스트 레이어 삽입
    │   │   └─ 메타데이터 설정
    │   │
    │   └─ 8.7 결과 저장 (100% 진행)
    │       └─ storage/output/{job_id}/{filename}_processed.pdf
    │
    ├─ 9. 상태 업데이트
    │   └─ "processing" → "completed" (또는 "failed")
    │
    └─ 10. WebSocket 알림
        └─ 클라이언트에 완료 이벤트 전송
    │
    ▼
[클라이언트]
    │
    └─ 11. 결과 다운로드
        └─ GET /api/jobs/{job_id}/result
```

#### 3.1.2 업스케일 상세 플로우

```python
def upscale_image(image: PIL.Image, scale: int, device: str) -> PIL.Image:
    """
    이미지 업스케일 처리
    
    Args:
        image: 입력 이미지 (PIL Image)
        scale: 업스케일 배율 (2 또는 4)
        device: 'cuda' 또는 'cpu'
    
    Returns:
        업스케일된 이미지
    """
    # 1. 이미지를 numpy 배열로 변환
    img_np = np.array(image)
    
    # 2. Real-ESRGAN 모델 로드 (캐시됨)
    model = load_realesrgan_model(scale=scale, device=device)
    
    # 3. 전처리: BGR 변환, 정규화
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    img_tensor = torch.from_numpy(img_bgr).float() / 255.0
    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0).to(device)
    
    # 4. 모델 추론
    with torch.no_grad():
        output_tensor = model(img_tensor)
    
    # 5. 후처리: 텐서 → numpy, 클리핑, BGR → RGB
    output_np = output_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
    output_np = np.clip(output_np * 255.0, 0, 255).astype(np.uint8)
    output_rgb = cv2.cvtColor(output_np, cv2.COLOR_BGR2RGB)
    
    # 6. PIL Image 변환
    result_image = Image.fromarray(output_rgb)
    
    return result_image
```

#### 3.1.3 워터마크 제거 상세 플로우

```python
def remove_watermark(image: PIL.Image, mode: str) -> PIL.Image:
    """
    워터마크 제거 처리
    
    Args:
        image: 입력 이미지
        mode: 'auto', 'template', 'segment'
    
    Returns:
        워터마크 제거된 이미지
    """
    # 1. 워터마크 마스크 생성
    if mode == 'auto':
        mask = detect_watermark_auto(image)
    elif mode == 'template':
        mask = detect_watermark_template(image)
    else:
        mask = detect_watermark_segment(image)
    
    # 2. 마스크 검증 (본문 텍스트 보호)
    mask = refine_mask(mask, image)
    
    # 3. LaMa 인페인팅 적용
    result = lama_inpaint(image, mask)
    
    return result

def detect_watermark_auto(image: PIL.Image) -> np.ndarray:
    """
    자동 워터마크 탐지
    - 반투명 영역 탐지
    - 반복 패턴 탐지
    - 색상 이상 영역 탐지
    """
    img_np = np.array(image)
    
    # 1. HSV 변환 및 채도 분석
    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    
    # 2. 엣지 검출 및 고주파 패턴 탐지
    edges = cv2.Canny(img_np, 50, 150)
    
    # 3. 템플릿 매칭으로 반복 패턴 찾기
    # (여러 페이지에서 공통 패턴 추출)
    
    # 4. 마스크 생성 (threshold + morphology)
    mask = create_mask_from_features(saturation, edges)
    
    return mask
```

#### 3.1.4 OCR 상세 플로우

```python
def ocr_image(image: PIL.Image, langs: str) -> List[Dict]:
    """
    이미지에서 텍스트 추출
    
    Args:
        image: 입력 이미지
        langs: 언어 코드 (예: 'kor+eng')
    
    Returns:
        [{text, bbox, confidence}, ...]
    """
    # 1. PaddleOCR 엔진 초기화
    ocr = PaddleOCR(use_angle_cls=True, lang='korean')
    
    # 2. OCR 실행
    result = ocr.ocr(np.array(image), cls=True)
    
    # 3. 결과 정규화
    normalized = []
    for line in result[0]:
        box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text = line[1][0]  # 텍스트
        conf = line[1][1]  # 신뢰도
        
        # bbox를 [x, y, w, h] 형식으로 변환
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        
        normalized.append({
            'text': text,
            'bbox': bbox,
            'confidence': conf
        })
    
    return normalized
```

### 3.2 에러 처리 플로우

```python
# 각 단계에서 발생 가능한 에러와 처리 방법

try:
    # 파이프라인 실행
    result = process_pipeline(job_id, file_path, options)
except PDFRasterizeError as e:
    # PDF 렌더링 실패 → 원본 PDF 손상 가능성
    logger.error(f"PDF rasterize failed: {e}")
    update_job_status(job_id, "failed", error="Invalid PDF file")
    
except GPUMemoryError as e:
    # GPU 메모리 부족 → CPU로 폴백 또는 배치 크기 감소
    logger.warning(f"GPU OOM, falling back to CPU: {e}")
    result = process_pipeline_cpu(job_id, file_path, options)
    
except ModelLoadError as e:
    # 모델 로드 실패 → 가중치 파일 누락 또는 손상
    logger.error(f"Model load failed: {e}")
    update_job_status(job_id, "failed", error="AI model unavailable")
    
except OCRError as e:
    # OCR 실패 → 경고만 로그, OCR 없이 PDF 생성
    logger.warning(f"OCR failed, skipping text layer: {e}")
    result = build_pdf_without_ocr(images)
    
except Exception as e:
    # 예상치 못한 에러 → 로그 + 사용자 알림
    logger.exception(f"Unexpected error in pipeline: {e}")
    update_job_status(job_id, "failed", error="Processing failed")
```

### 3.3 GPU 자동 인식 플로우

```python
def get_optimal_device() -> torch.device:
    """
    최적의 디바이스 선택
    
    Returns:
        torch.device ('cuda:0' 또는 'cpu')
    """
    # 1. 환경 변수 확인
    use_gpu = os.getenv('USE_GPU', 'auto')
    
    if use_gpu == 'false':
        return torch.device('cpu')
    
    if use_gpu == 'true':
        if not torch.cuda.is_available():
            logger.warning("GPU requested but CUDA not available, using CPU")
            return torch.device('cpu')
        return torch.device('cuda:0')
    
    # 2. auto 모드: 자동 감지
    if not torch.cuda.is_available():
        logger.info("CUDA not available, using CPU")
        return torch.device('cpu')
    
    # 3. nvidia-smi 확인
    try:
        subprocess.run(['nvidia-smi'], capture_output=True, check=True)
        logger.info("GPU detected, using CUDA")
        return torch.device('cuda:0')
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("nvidia-smi not found, using CPU")
        return torch.device('cpu')
```

---

## 4. API 명세서

### 4.1 Base URL

- **개발 환경**: `http://localhost:8000/api`
- **운영 환경**: 환경 변수 `API_BASE_URL`에서 로드

### 4.2 인증

현재 버전에서는 인증 미구현. 향후 JWT 토큰 기반 인증 추가 예정.

### 4.3 공통 응답 형식

#### 성공 응답
```json
{
  "success": true,
  "data": { ... },
  "message": "Success"
}
```

#### 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File size exceeds limit",
    "details": { ... }
  }
}
```

### 4.4 엔드포인트

#### 4.4.1 헬스 체크

**GET** `/health`

서버 상태 확인

**응답**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "redis": "connected",
    "gpu": "available"
  }
}
```

#### 4.4.2 작업 생성 (파일 업로드)

**POST** `/jobs`

PDF 파일 업로드 및 처리 작업 생성

**요청**
- Content-Type: `multipart/form-data`

**Form Data**
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| files | File[] | Y | PDF 파일 (최대 10개, 각 250MB 이하) |
| upscale | boolean | N | 업스케일 활성화 (기본값: true) |
| upscale_scale | int | N | 업스케일 배율 (2 또는 4, 기본값: 2) |
| watermark | boolean | N | 워터마크 제거 활성화 (기본값: true) |
| watermark_mode | string | N | 워터마크 제거 모드 ('auto', 'template', 'segment', 기본값: 'auto') |
| ocr | boolean | N | OCR 활성화 (기본값: true) |
| ocr_langs | string | N | OCR 언어 (기본값: 'kor+eng') |
| pdfa | boolean | N | PDF/A 표준 준수 (기본값: false) |

**응답**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "queued",
    "created_at": "2025-10-21T12:00:00Z",
    "files": [
      {
        "filename": "document.pdf",
        "size": 5242880,
        "pages": 10
      }
    ],
    "options": {
      "upscale": true,
      "upscale_scale": 2,
      "watermark": true,
      "watermark_mode": "auto",
      "ocr": true,
      "ocr_langs": "kor+eng"
    }
  }
}
```

**에러 코드**
- `400 BAD_REQUEST`: 잘못된 요청 (파일 없음, 형식 오류)
- `413 PAYLOAD_TOO_LARGE`: 파일 크기 초과
- `415 UNSUPPORTED_MEDIA_TYPE`: PDF 파일이 아님
- `500 INTERNAL_SERVER_ERROR`: 서버 에러

#### 4.4.3 작업 상태 조회

**GET** `/jobs/{job_id}`

작업 진행 상황 및 상태 조회

**경로 매개변수**
- `job_id`: 작업 ID (UUID)

**응답**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "progress": 65,
    "current_step": "watermark_removal",
    "steps": [
      {
        "name": "rasterize",
        "status": "completed",
        "progress": 100
      },
      {
        "name": "preprocess",
        "status": "completed",
        "progress": 100
      },
      {
        "name": "upscale",
        "status": "completed",
        "progress": 100
      },
      {
        "name": "watermark",
        "status": "processing",
        "progress": 50
      },
      {
        "name": "ocr",
        "status": "pending",
        "progress": 0
      },
      {
        "name": "pdf_generation",
        "status": "pending",
        "progress": 0
      }
    ],
    "created_at": "2025-10-21T12:00:00Z",
    "started_at": "2025-10-21T12:00:05Z",
    "estimated_completion": "2025-10-21T12:02:30Z"
  }
}
```

**상태 값**
- `queued`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `failed`: 실패
- `cancelled`: 취소됨

#### 4.4.4 작업 취소

**DELETE** `/jobs/{job_id}`

진행 중인 작업 취소

**경로 매개변수**
- `job_id`: 작업 ID

**응답**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled"
  }
}
```

#### 4.4.5 결과 다운로드

**GET** `/jobs/{job_id}/result`

처리된 PDF 파일 다운로드

**경로 매개변수**
- `job_id`: 작업 ID

**쿼리 매개변수**
- `filename` (선택): 다운로드 파일명 지정

**응답**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="document_processed.pdf"`
- Body: PDF 파일 바이너리

**에러 코드**
- `404 NOT_FOUND`: 작업 또는 결과 파일 없음
- `409 CONFLICT`: 작업이 아직 완료되지 않음

#### 4.4.6 WebSocket: 실시간 진행률

**WS** `/jobs/{job_id}/progress`

실시간 작업 진행률 스트리밍

**연결**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/jobs/{job_id}/progress');
```

**메시지 형식**
```json
{
  "type": "progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 65,
  "current_step": "watermark_removal",
  "message": "Removing watermark from page 5/10",
  "timestamp": "2025-10-21T12:01:30Z"
}
```

**이벤트 타입**
- `progress`: 진행률 업데이트
- `completed`: 작업 완료
- `failed`: 작업 실패
- `cancelled`: 작업 취소

#### 4.4.7 작업 목록 조회

**GET** `/jobs`

작업 목록 조회 (페이지네이션)

**쿼리 매개변수**
| 매개변수 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | N | 페이지 번호 (기본값: 1) |
| limit | int | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| status | string | N | 상태 필터 ('queued', 'processing', 'completed', 'failed') |
| sort | string | N | 정렬 기준 ('created_at', 'updated_at', 기본값: 'created_at') |
| order | string | N | 정렬 순서 ('asc', 'desc', 기본값: 'desc') |

**응답**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "job_id": "...",
        "status": "completed",
        "progress": 100,
        "created_at": "2025-10-21T12:00:00Z",
        "completed_at": "2025-10-21T12:02:45Z",
        "files_count": 2
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

### 4.5 에러 코드 목록

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| VALIDATION_ERROR | 400 | 요청 데이터 검증 실패 |
| FILE_TOO_LARGE | 413 | 파일 크기 초과 |
| INVALID_FILE_TYPE | 415 | 지원하지 않는 파일 형식 |
| JOB_NOT_FOUND | 404 | 작업을 찾을 수 없음 |
| JOB_NOT_COMPLETED | 409 | 작업이 아직 완료되지 않음 |
| PROCESSING_ERROR | 500 | 처리 중 에러 발생 |
| MODEL_UNAVAILABLE | 503 | AI 모델을 사용할 수 없음 |
| QUEUE_FULL | 503 | 작업 큐가 가득 참 |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-10-21 | 1.0.0 | 초기 청사진 작성 |

---

## 향후 계획

### Phase 2 (v2.0)
- 사용자 인증 및 권한 관리
- 작업 우선순위 설정
- 웹훅 알림
- S3 호환 스토리지 지원
- 배치 작업 API

### Phase 3 (v3.0)
- 문서 레이아웃 분석
- 표 구조 인식 및 추출
- 다국어 OCR 확장 (중국어, 일본어)
- 문서 분류 및 태깅
- 검색 엔진 통합

### Phase 4 (v4.0)
- 대용량 문서 처리 (1000+ 페이지)
- 분산 처리 (Kubernetes)
- 모델 A/B 테스팅
- 품질 메트릭 대시보드

