/**
 * 처리 상태 컴포넌트
 * 
 * 작업 진행률 및 상태 표시
 */

import { Download, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import type { TaskStatus } from '../types';

interface ProcessingStatusProps {
  taskStatus: TaskStatus;
  onDownload: () => void;
  onReset: () => void;
}

export default function ProcessingStatus({
  taskStatus,
  onDownload,
  onReset,
}: ProcessingStatusProps) {
  const getStatusIcon = () => {
    switch (taskStatus.status) {
      case 'pending':
      case 'processing':
        return <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-12 h-12 text-green-500" />;
      case 'failed':
        return <XCircle className="w-12 h-12 text-red-500" />;
    }
  };

  const getStatusText = () => {
    switch (taskStatus.status) {
      case 'pending':
        return '대기 중...';
      case 'processing':
        return '처리 중...';
      case 'completed':
        return '완료!';
      case 'failed':
        return '실패';
    }
  };

  const getStatusColor = () => {
    switch (taskStatus.status) {
      case 'pending':
      case 'processing':
        return 'text-blue-600 dark:text-blue-400';
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'failed':
        return 'text-red-600 dark:text-red-400';
    }
  };

  return (
    <div className="w-full bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <div className="flex flex-col items-center gap-6">
        {/* 아이콘 */}
        <div className="flex items-center justify-center">
          {getStatusIcon()}
        </div>

        {/* 상태 텍스트 */}
        <div className="text-center">
          <h3 className={`text-2xl font-bold ${getStatusColor()}`}>
            {getStatusText()}
          </h3>
          {taskStatus.message && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {taskStatus.message}
            </p>
          )}
        </div>

        {/* 진행률 바 */}
        {(taskStatus.status === 'pending' || taskStatus.status === 'processing') && (
          <div className="w-full">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
              <span>진행률</span>
              <span>{taskStatus.progress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
              <div
                className="bg-blue-500 h-full transition-all duration-300 ease-out rounded-full"
                style={{ width: `${taskStatus.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* 에러 메시지 */}
        {taskStatus.status === 'failed' && taskStatus.error && (
          <div className="w-full p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">
              {taskStatus.error}
            </p>
          </div>
        )}

        {/* 완료 정보 */}
        {taskStatus.status === 'completed' && taskStatus.file_size && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            파일 크기: {(taskStatus.file_size / 1024 / 1024).toFixed(2)} MB
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="flex gap-4">
          {taskStatus.status === 'completed' && (
            <button
              onClick={onDownload}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700
                       text-white font-semibold rounded-lg transition-colors
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <Download className="w-5 h-5" />
              다운로드
            </button>
          )}

          <button
            onClick={onReset}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600
                     text-gray-900 dark:text-gray-100 font-semibold rounded-lg transition-colors
                     focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            {taskStatus.status === 'completed' || taskStatus.status === 'failed'
              ? '새 파일 처리'
              : '취소'}
          </button>
        </div>

        {/* 작업 ID */}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          작업 ID: {taskStatus.task_id}
        </div>
      </div>
    </div>
  );
}

