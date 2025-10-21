# PDF Upgrade Frontend

React + TypeScript + Vite 기반 프론트엔드

## 🚀 시작하기

### 의존성 설치

```bash
npm install
```

### 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 빌드

```bash
npm run build
```

### 미리보기

```bash
npm run preview
```

## 🛠 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Vite** - 빠른 번들러
- **TailwindCSS** - 유틸리티 CSS
- **React Query** - 서버 상태 관리
- **Axios** - HTTP 클라이언트
- **React Dropzone** - 파일 드래그앤드롭
- **Lucide React** - 아이콘

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/        # React 컴포넌트
│   │   ├── FileUpload.tsx
│   │   ├── OptionsForm.tsx
│   │   └── ProcessingStatus.tsx
│   ├── services/          # API 서비스
│   │   └── api.ts
│   ├── types/             # TypeScript 타입
│   │   └── index.ts
│   ├── App.tsx            # 메인 앱
│   ├── main.tsx           # 엔트리 포인트
│   └── index.css          # 글로벌 스타일
├── public/                # 정적 파일
├── index.html             # HTML 템플릿
├── vite.config.ts         # Vite 설정
├── tailwind.config.js     # TailwindCSS 설정
├── tsconfig.json          # TypeScript 설정
└── package.json           # 의존성
```

## ⚙️ 환경 변수

`.env.example`을 `.env`로 복사하고 설정:

```env
VITE_API_URL=http://localhost:8000
```

## 📝 주요 기능

1. **파일 업로드**
   - 드래그앤드롭 지원
   - PDF 파일만 허용
   - 최대 250MB

2. **옵션 설정**
   - 이미지 전처리
   - 고해상도 업스케일 (2x/4x)
   - 워터마크 자동 제거
   - OCR 텍스트 인식

3. **실시간 진행률**
   - 2초 간격 폴링
   - 진행률 바 표시
   - 상태 메시지

4. **결과 다운로드**
   - 처리 완료 후 다운로드
   - 파일명 자동 설정

## 🔧 개발

### Linting

```bash
npm run lint
```

### 타입 체크

```bash
npx tsc --noEmit
```

## 📦 배포

### 빌드 최적화

```bash
npm run build
```

### 정적 호스팅

빌드된 `dist` 폴더를 다음과 같은 플랫폼에 배포:

- **Vercel**
- **Netlify**
- **GitHub Pages**
- **Nginx/Apache**

## 🎨 커스터마이징

### 색상 변경

`tailwind.config.js`에서 테마 커스터마이징:

```js
theme: {
  extend: {
    colors: {
      primary: '#your-color',
    },
  },
},
```

### API 엔드포인트 변경

`src/services/api.ts`에서 `API_BASE_URL` 수정

## 📄 라이센스

MIT License

