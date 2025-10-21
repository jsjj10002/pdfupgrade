# PDF Upgrade 배포 가이드

완전한 Docker 기반 배포 가이드

## 📋 목차

- [사전 요구사항](#사전-요구사항)
- [GPU 환경 설정](#gpu-환경-설정)
- [배포 방법](#배포-방법)
- [환경 변수 설정](#환경-변수-설정)
- [트러블슈팅](#트러블슈팅)

## 🔧 사전 요구사항

### 필수

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **최소 시스템 요구사항**:
  - CPU: 4코어 이상
  - RAM: 8GB 이상
  - 디스크: 20GB 이상 여유 공간

### GPU 사용 시 (선택적)

- **NVIDIA GPU**: CUDA 지원 GPU
- **NVIDIA Driver**: 최신 버전
- **NVIDIA Container Toolkit**: 설치 필요

## 🎮 GPU 환경 설정

### 1. NVIDIA Driver 설치

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y nvidia-driver-535

# 설치 확인
nvidia-smi
```

### 2. NVIDIA Container Toolkit 설치

```bash
# 저장소 추가
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 설치
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Docker 재시작
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

### 3. Docker Compose에서 GPU 사용

`docker-compose.yml`에 이미 GPU 설정이 포함되어 있다:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

## 🚀 배포 방법

### 방법 1: GPU 사용 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/jsjj10002/pdfupgrade.git
cd pdfupgrade

# 2. 환경 변수 설정
cp env.example.txt .env
# .env 파일 편집 (아래 섹션 참조)

# 3. Docker 이미지 빌드 및 실행
docker-compose up -d --build

# 4. 로그 확인
docker-compose logs -f

# 5. 서비스 접속
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 방법 2: CPU 전용

GPU가 없거나 사용하지 않는 경우:

```bash
# CPU 전용 docker-compose 사용
docker-compose -f docker-compose.cpu.yml up -d --build
```

### 배포 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 헬스 체크
curl http://localhost:8000/health
curl http://localhost/

# GPU 사용 확인 (GPU 환경)
docker exec pdfupgrade-backend nvidia-smi
```

## ⚙️ 환경 변수 설정

`.env` 파일 예시:

```bash
# 애플리케이션
APP_ENV=production
LOG_LEVEL=INFO

# GPU 설정
USE_GPU=auto                    # auto|true|false
CUDA_VISIBLE_DEVICES=0          # 사용할 GPU ID

# 파일 제한
MAX_FILE_SIZE_MB=250

# 기능 활성화
UPSCALE_ENABLED=true
WATERMARK_ENABLED=true
OCR_ENABLED=true

# CORS (프로덕션에서는 실제 도메인으로 변경)
ALLOWED_ORIGINS=http://localhost,http://your-domain.com
```

## 🔄 업데이트

```bash
# 1. 최신 코드 가져오기
git pull origin main

# 2. 컨테이너 중지 및 재빌드
docker-compose down
docker-compose up -d --build

# 3. 이전 이미지 정리 (선택적)
docker image prune -f
```

## 🛠 유지보수

### 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend

# 최근 100줄
docker-compose logs --tail=100 backend
```

### 데이터 백업

```bash
# 스토리지 백업
tar -czf backup-storage-$(date +%Y%m%d).tar.gz storage/

# 로그 백업
tar -czf backup-logs-$(date +%Y%m%d).tar.gz logs/
```

### 리소스 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 디스크 사용량
docker system df
```

### 정리

```bash
# 컨테이너 중지 및 제거
docker-compose down

# 볼륨까지 제거 (주의: 데이터 삭제)
docker-compose down -v

# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a
```

## 🐛 트러블슈팅

### GPU가 인식되지 않음

```bash
# NVIDIA 드라이버 확인
nvidia-smi

# Docker에서 GPU 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 로그 확인
docker-compose logs backend | grep GPU
```

### 메모리 부족

```yaml
# docker-compose.yml에 메모리 제한 추가
services:
  backend:
    mem_limit: 8g
    memswap_limit: 8g
```

### 포트 충돌

```bash
# 포트 변경
# docker-compose.yml에서:
ports:
  - "8080:8000"  # 백엔드
  - "8081:80"    # 프론트엔드
```

### 파일 업로드 실패

```bash
# NGINX 업로드 크기 확인 (nginx.conf)
client_max_body_size 250M;

# 환경 변수 확인
MAX_FILE_SIZE_MB=250
```

### 컨테이너 재시작 반복

```bash
# 로그에서 원인 파악
docker-compose logs --tail=50 backend

# 헬스체크 비활성화 (임시)
# docker-compose.yml에서 healthcheck: 부분 주석 처리
```

## 🌐 프로덕션 배포

### 도메인 연결

1. **DNS 설정**: A 레코드로 서버 IP 연결
2. **HTTPS 설정**: Let's Encrypt + Certbot

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo certbot renew --dry-run
```

3. **nginx.conf 수정**:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... 나머지 설정
}
```

### 보안 강화

1. **방화벽 설정**:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **환경 변수 보안**:
   - `.env` 파일 권한 제한: `chmod 600 .env`
   - 프로덕션 시크릿 사용

3. **정기 업데이트**:
```bash
# 시스템 업데이트
sudo apt-get update && sudo apt-get upgrade -y

# Docker 이미지 업데이트
docker-compose pull
docker-compose up -d
```

## 📊 모니터링

### Prometheus + Grafana (향후)

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 로그 집계

```bash
# 로그를 파일로 저장
docker-compose logs > logs/docker-$(date +%Y%m%d).log
```

## 💡 성능 최적화

### 1. 모델 캐싱

모델을 볼륨으로 마운트하여 재사용:

```yaml
volumes:
  - ./app/models:/app/models
```

### 2. 워커 수 조정

```yaml
environment:
  - MAX_CONCURRENCY=4  # CPU 코어 수에 맞게 조정
```

### 3. Redis 추가 (향후)

```yaml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [FastAPI 배포](https://fastapi.tiangolo.com/deployment/)

## 🆘 지원

문제가 발생하면 GitHub Issues에 보고:
https://github.com/jsjj10002/pdfupgrade/issues

---

**작성일**: 2025-10-21  
**버전**: 1.0.0

