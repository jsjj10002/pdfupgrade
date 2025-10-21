/**
 * API 타입 정의
 */

export interface ProcessOptions {
  // 래스터화
  dpi?: number;

  // 전처리
  preprocess?: boolean;
  deskew?: boolean;
  white_balance?: boolean;
  enhance_contrast?: boolean;
  denoise?: boolean;

  // 업스케일
  upscale?: boolean;
  upscale_scale?: 2 | 4;
  face_enhance?: boolean;

  // 워터마크 제거
  watermark?: boolean;
  watermark_method?: 'auto' | 'opencv';
  watermark_threshold?: number;
  watermark_protect_text?: boolean;

  // OCR
  ocr?: boolean;
  ocr_engine?: 'paddle' | 'tesseract';
  ocr_langs?: string;
  ocr_min_confidence?: number;

  // PDF 출력
  pdfa?: boolean;
  compression?: boolean;
}

export interface ProcessRequest {
  options: ProcessOptions;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  result_file?: string;
  file_size?: number;
  error?: string;
}

export interface TaskCreateResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface FileUploadResponse {
  filename: string;
  size: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  gpu_available: boolean;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: string;
}

