/**
 * 파일 업로드 컴포넌트
 * 
 * 드래그앤드롭 지원 PDF 파일 업로드
 */

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export default function FileUpload({ onFileSelect, selectedFile, disabled }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled,
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          {selectedFile ? (
            <>
              <FileText className="w-16 h-16 text-blue-500" />
              <div>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </>
          ) : (
            <>
              <Upload className="w-16 h-16 text-gray-400" />
              <div>
                <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {isDragActive
                    ? 'PDF 파일을 여기에 놓으세요'
                    : 'PDF 파일을 드래그하거나 클릭하여 선택'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  최대 250MB까지 지원
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {selectedFile && !disabled && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFileSelect(null as any);
          }}
          className="mt-4 text-sm text-red-600 hover:text-red-700 dark:text-red-400"
        >
          파일 제거
        </button>
      )}
    </div>
  );
}

