/**
 * 메인 App 컴포넌트
 */

import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { FileUp } from 'lucide-react';
import FileUpload from './components/FileUpload';
import OptionsForm from './components/OptionsForm';
import ProcessingStatus from './components/ProcessingStatus';
import {
  uploadFile,
  createProcessTask,
  getTaskStatus,
  downloadResult,
  checkHealth,
} from './services/api';
import type { ProcessOptions, TaskStatus } from './types';

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [options, setOptions] = useState<ProcessOptions>({
    dpi: 300,
    preprocess: true,
    deskew: true,
    white_balance: true,
    enhance_contrast: true,
    upscale: false,
    upscale_scale: 2,
    watermark: false,
    ocr: false,
    ocr_engine: 'paddle',
    ocr_langs: 'kor+eng',
    pdfa: false,
    compression: true,
  });

  // 헬스 체크
  const { data: health } = useQuery('health', checkHealth, {
    refetchInterval: 30000,
  });

  // 작업 상태 폴링
  const { data: taskStatus, refetch: refetchTaskStatus } = useQuery<TaskStatus>(
    ['taskStatus', taskId],
    () => getTaskStatus(taskId!),
    {
      enabled: !!taskId,
      refetchInterval: (data) => {
        if (data?.status === 'pending' || data?.status === 'processing') {
          return 2000; // 2초마다 폴링
        }
        return false; // 완료되면 폴링 중지
      },
    }
  );

  // 파일 업로드 처리
  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      const response = await uploadFile(selectedFile);
      setUploadedFilename(response.filename);
      alert('파일이 업로드되었습니다!');
    } catch (error: any) {
      console.error('업로드 실패:', error);
      alert(`업로드 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // 처리 시작
  const handleProcess = async () => {
    if (!uploadedFilename) return;

    try {
      setIsProcessing(true);
      const response = await createProcessTask(uploadedFilename, { options });
      setTaskId(response.task_id);
    } catch (error: any) {
      console.error('처리 실패:', error);
      alert(`처리 실패: ${error.response?.data?.detail || error.message}`);
      setIsProcessing(false);
    }
  };

  // 결과 다운로드
  const handleDownload = async () => {
    if (!taskId) return;

    try {
      const blob = await downloadResult(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed_${uploadedFilename}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('다운로드 실패:', error);
      alert(`다운로드 실패: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 리셋
  const handleReset = () => {
    setSelectedFile(null);
    setUploadedFilename(null);
    setTaskId(null);
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <FileUp className="w-12 h-12 text-blue-600 dark:text-blue-400" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
              PDF Upgrade
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            AI 기반 PDF 고품질 변환 서비스
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            저화질 업스케일 | 워터마크 제거 | OCR 텍스트 인식
          </p>
          {health && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-green-100 dark:bg-green-900/30 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-green-800 dark:text-green-200">
                서버 정상 {health.gpu_available && '• GPU 사용 가능'}
              </span>
            </div>
          )}
        </header>

        {/* 메인 컨텐츠 */}
        <div className="space-y-8">
          {!taskId ? (
            <>
              {/* 파일 업로드 */}
              <FileUpload
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile}
                disabled={isUploading || !!uploadedFilename}
              />

              {/* 업로드 버튼 */}
              {selectedFile && !uploadedFilename && (
                <div className="flex justify-center">
                  <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
                             text-white font-semibold rounded-lg transition-colors
                             focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                             disabled:cursor-not-allowed"
                  >
                    {isUploading ? '업로드 중...' : '파일 업로드'}
                  </button>
                </div>
              )}

              {/* 옵션 설정 */}
              {uploadedFilename && (
                <>
                  <OptionsForm
                    options={options}
                    onChange={setOptions}
                    disabled={isProcessing}
                  />

                  {/* 처리 시작 버튼 */}
                  <div className="flex justify-center gap-4">
                    <button
                      onClick={handleProcess}
                      disabled={isProcessing}
                      className="px-8 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400
                               text-white font-semibold rounded-lg transition-colors
                               focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
                               disabled:cursor-not-allowed"
                    >
                      {isProcessing ? '처리 시작 중...' : '처리 시작'}
                    </button>
                    <button
                      onClick={handleReset}
                      disabled={isProcessing}
                      className="px-8 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600
                               text-gray-900 dark:text-gray-100 font-semibold rounded-lg transition-colors
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      취소
                    </button>
                  </div>
                </>
              )}
            </>
          ) : (
            /* 처리 상태 */
            taskStatus && (
              <ProcessingStatus
                taskStatus={taskStatus}
                onDownload={handleDownload}
                onReset={handleReset}
              />
            )
          )}
        </div>

        {/* 푸터 */}
        <footer className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            © 2025 PDF Upgrade. AI 기반 PDF 처리 서비스.
          </p>
          <p className="mt-2">
            Real-ESRGAN • PaddleOCR • OpenCV • FastAPI • React
          </p>
        </footer>
      </div>
    </div>
  );
}

