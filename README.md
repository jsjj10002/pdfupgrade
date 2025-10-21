# PDF Upgrade

AI 기반 PDF 품질 개선 플랫폼

## 주요 기능

- **고해상도 업스케일**: Real-ESRGAN을 이용한 이미지 품질 개선
- **워터마크 자동 제거**: LaMa 인페인팅 기반 워터마크 제거
- **OCR 텍스트 레이어 생성**: PaddleOCR을 이용한 검색 가능한 PDF 생성
- **배치 처리**: 여러 파일 동시 처리 지원
- **GPU 자동 인식**: CUDA 환경 자동 감지 및 활용

## 기술 스택

### 백엔드
- Python 3.11+
- FastAPI
- Celery + Redis
- PyTorch
- Real-ESRGAN, LaMa
- PaddleOCR
- PyMuPDF

### 프론트엔드
- React
- TypeScript
- Vite
- TailwindCSS

### 인프라
- Docker
- NVIDIA Container Toolkit
- Redis

## 개발 환경 설정

### 사전 요구사항
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 패키지 매니저
- Node.js 18+
- Redis (Docker 또는 로컬)
- (선택) NVIDIA GPU + CUDA 12.1+

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd pdfupgrade

# Python 환경 설정 (uv 사용)
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 입력

# 프론트엔드 설치
cd frontend
npm install
```

### 실행

```bash
# 백엔드 API 서버
uv run uvicorn app.api.main:app --reload

# Celery Worker
uv run celery -A app.workers.celery_app worker --loglevel=info

# 프론트엔드 (개발 모드)
cd frontend
npm run dev
```

## Git-Flow 전략

- `main`: 프로덕션 배포용 브랜치
- `develop`: 개발 통합 브랜치
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치
- `release/*`: 배포 준비 브랜치

## 문서

- [프로젝트 청사진](doc/PROJECT_BLUEPRINT.md)
- [개발 규칙](.rules)
- [API 명세서](doc/API_SPEC.md)

## 라이선스

MIT License

