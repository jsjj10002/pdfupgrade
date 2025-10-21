# PDF Upgrade 🚀

**AI 기반 PDF 고품질 변환 웹 애플리케이션**

저화질 PDF를 고화질로 업스케일하고, 워터마크를 자동으로 제거하며, OCR로 검색 가능하게 만드는 완전한 풀스택 웹 서비스

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 주요 기능

- **🎨 고해상도 업스케일**: Real-ESRGAN을 이용한 2x/4x 이미지 업스케일
- **🧹 워터마크 자동 제거**: 다중 알고리즘 기반 지능형 워터마크 탐지 및 제거
- **📝 OCR 텍스트 인식**: PaddleOCR로 한글+영문 텍스트 인식 및 검색 가능한 PDF 생성
- **⚡ GPU 가속**: NVIDIA GPU 자동 감지 및 활용
- **🌐 웹 인터페이스**: 드래그앤드롭 업로드, 실시간 진행률 표시
- **🐳 Docker 지원**: 원클릭 배포, GPU/CPU 모두 지원

## 🎬 데모

```
웹 브라우저 → PDF 업로드 → 옵션 선택 → 실시간 처리 → 고품질 PDF 다운로드
```

## 🚀 빠른 시작

### Docker Compose로 실행 (권장)

```bash
# 저장소 클론
git clone https://github.com/jsjj10002/pdfupgrade.git
cd pdfupgrade

# GPU 환경
docker-compose up -d

# CPU 환경
docker-compose -f docker-compose.cpu.yml up -d

# 접속
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 로컬 개발 환경

#### 백엔드

```bash
# Python 환경 설정 (uv 사용)
uv sync --extra ai

# 서버 실행
uvicorn app.api.main:app --reload
```

#### 프론트엔드

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 📋 사전 요구사항

### Docker 사용 시
- Docker 20.10+
- Docker Compose 2.0+
- (선택) NVIDIA GPU + NVIDIA Container Toolkit

### 로컬 개발 시
- Python 3.11+
- Node.js 20+
- (선택) NVIDIA GPU + CUDA 12.1+

## 🏗 아키텍처

```
┌─────────────────────────────┐
│   React Frontend (Vite)     │
│  - 드래그앤드롭 업로드       │
│  - 실시간 진행률             │
│  - TailwindCSS              │
└──────────┬──────────────────┘
           │ REST API
┌──────────▼──────────────────┐
│   FastAPI Backend           │
│  - 파일 업로드/다운로드      │
│  - 작업 큐 관리              │
│  - 상태 추적                 │
└──────────┬──────────────────┘
           │
┌──────────▼──────────────────┐
│   PDF 처리 파이프라인       │
│  - 래스터화 (PyMuPDF)       │
│  - 전처리 (OpenCV)          │
│  - 업스케일 (Real-ESRGAN)   │
│  - 워터마크 제거             │
│  - OCR (PaddleOCR)          │
│  - PDF 생성                 │
└─────────────────────────────┘
```

## 🛠 기술 스택

### 백엔드
- **FastAPI**: 고성능 REST API
- **PyTorch**: AI 모델 실행
- **Real-ESRGAN**: 이미지 업스케일
- **PaddleOCR**: 텍스트 인식
- **OpenCV**: 이미지 처리
- **PyMuPDF**: PDF 조작

### 프론트엔드
- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안전성
- **Vite**: 빠른 개발 서버
- **TailwindCSS**: 스타일링
- **React Query**: 서버 상태 관리
- **Axios**: HTTP 클라이언트

### 인프라
- **Docker**: 컨테이너화
- **NGINX**: 리버스 프록시
- **NVIDIA Container Toolkit**: GPU 지원

## 📖 문서

- [프로젝트 청사진](doc/PROJECT_BLUEPRINT.md)
- [배포 가이드](DEPLOYMENT.md)
- [Sprint 요약](doc/)
  - [Sprint 1: PDF 래스터화](doc/SPRINT1_SUMMARY.md)
  - [Sprint 2: 업스케일](doc/SPRINT2_SUMMARY.md)
  - [Sprint 3: OCR](doc/SPRINT3_SUMMARY.md)
  - [Sprint 4: 워터마크 제거](doc/SPRINT4_SUMMARY.md)
  - [Sprint 5: FastAPI 서버](doc/SPRINT5_SUMMARY.md)
  - [Sprint 6: React 프론트엔드](doc/SPRINT6_SUMMARY.md)
  - [Sprint 7: Docker 배포](doc/SPRINT7_SUMMARY.md)

## ⚙️ 환경 변수

`.env.example`을 `.env`로 복사하고 설정:

```bash
# 애플리케이션
APP_ENV=production
LOG_LEVEL=INFO

# GPU 설정
USE_GPU=auto                    # auto|true|false
CUDA_VISIBLE_DEVICES=0

# 기능 활성화
UPSCALE_ENABLED=true
WATERMARK_ENABLED=true
OCR_ENABLED=true

# 파일 제한
MAX_FILE_SIZE_MB=250
```

## 📊 성능

### GPU 처리 시간 (RTX 3090 기준)
- **래스터화**: ~1초
- **업스케일 (2x)**: ~3초
- **워터마크 제거**: ~2초
- **OCR**: ~2초
- **총 처리 시간**: ~8초 (10페이지 PDF)

### CPU 처리 시간 (8코어 기준)
- **래스터화**: ~2초
- **워터마크 제거**: ~5초
- **OCR**: ~8초
- **총 처리 시간**: ~15초 (업스케일 제외)

## 🤝 기여

기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 팀

PDF Upgrade Team

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [React](https://github.com/facebook/react)

## 📧 문의

프로젝트에 대한 문의사항이 있으시면 GitHub Issues를 이용해주세요.

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**
