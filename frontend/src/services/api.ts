/**
 * API 서비스
 * 
 * FastAPI 백엔드와의 통신을 담당
 */

import axios from 'axios';
import type {
  ProcessRequest,
  TaskStatus,
  TaskCreateResponse,
  FileUploadResponse,
  HealthResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 헬스 체크
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

/**
 * 파일 업로드
 */
export const uploadFile = async (file: File): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<FileUploadResponse>('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * 처리 작업 생성
 */
export const createProcessTask = async (
  filename: string,
  request: ProcessRequest
): Promise<TaskCreateResponse> => {
  const response = await api.post<TaskCreateResponse>(
    `/api/process/${filename}`,
    request
  );
  return response.data;
};

/**
 * 작업 상태 조회
 */
export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get<TaskStatus>(`/api/tasks/${taskId}`);
  return response.data;
};

/**
 * 결과 다운로드
 */
export const downloadResult = async (taskId: string): Promise<Blob> => {
  const response = await api.get(`/api/tasks/${taskId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

/**
 * 작업 삭제
 */
export const deleteTask = async (taskId: string): Promise<void> => {
  await api.delete(`/api/tasks/${taskId}`);
};

export default api;

