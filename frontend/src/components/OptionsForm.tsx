/**
 * 옵션 설정 폼 컴포넌트
 * 
 * PDF 처리 옵션을 선택하는 폼
 */

import { Settings } from 'lucide-react';
import type { ProcessOptions } from '../types';

interface OptionsFormProps {
  options: ProcessOptions;
  onChange: (options: ProcessOptions) => void;
  disabled?: boolean;
}

export default function OptionsForm({ options, onChange, disabled }: OptionsFormProps) {
  const updateOption = <K extends keyof ProcessOptions>(
    key: K,
    value: ProcessOptions[K]
  ) => {
    onChange({ ...options, [key]: value });
  };

  return (
    <div className="w-full bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-6">
        <Settings className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
          처리 옵션
        </h2>
      </div>

      <div className="space-y-6">
        {/* 전처리 */}
        <section>
          <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">
            이미지 전처리
          </h3>
          <div className="space-y-2">
            <CheckboxOption
              label="기울기 보정"
              checked={options.deskew ?? true}
              onChange={(checked) => updateOption('deskew', checked)}
              disabled={disabled}
            />
            <CheckboxOption
              label="화이트 밸런스"
              checked={options.white_balance ?? true}
              onChange={(checked) => updateOption('white_balance', checked)}
              disabled={disabled}
            />
            <CheckboxOption
              label="대비 향상"
              checked={options.enhance_contrast ?? true}
              onChange={(checked) => updateOption('enhance_contrast', checked)}
              disabled={disabled}
            />
          </div>
        </section>

        {/* 업스케일 */}
        <section>
          <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">
            고해상도 업스케일
          </h3>
          <div className="space-y-3">
            <CheckboxOption
              label="업스케일 활성화"
              checked={options.upscale ?? false}
              onChange={(checked) => updateOption('upscale', checked)}
              disabled={disabled}
            />
            {options.upscale && (
              <>
                <div className="ml-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    배율
                  </label>
                  <select
                    value={options.upscale_scale ?? 2}
                    onChange={(e) =>
                      updateOption('upscale_scale', Number(e.target.value) as 2 | 4)
                    }
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                             disabled:opacity-50"
                  >
                    <option value={2}>2x (빠름)</option>
                    <option value={4}>4x (느림, 고품질)</option>
                  </select>
                </div>
                <div className="ml-6">
                  <CheckboxOption
                    label="얼굴 보정 (GFPGAN)"
                    checked={options.face_enhance ?? false}
                    onChange={(checked) => updateOption('face_enhance', checked)}
                    disabled={disabled}
                  />
                </div>
              </>
            )}
          </div>
        </section>

        {/* 워터마크 제거 */}
        <section>
          <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">
            워터마크 제거
          </h3>
          <div className="space-y-2">
            <CheckboxOption
              label="워터마크 자동 제거"
              checked={options.watermark ?? false}
              onChange={(checked) => updateOption('watermark', checked)}
              disabled={disabled}
            />
            {options.watermark && (
              <div className="ml-6">
                <CheckboxOption
                  label="본문 텍스트 보호"
                  checked={options.watermark_protect_text ?? true}
                  onChange={(checked) => updateOption('watermark_protect_text', checked)}
                  disabled={disabled}
                />
              </div>
            )}
          </div>
        </section>

        {/* OCR */}
        <section>
          <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">
            텍스트 인식 (OCR)
          </h3>
          <div className="space-y-3">
            <CheckboxOption
              label="OCR 활성화 (검색 가능한 PDF)"
              checked={options.ocr ?? false}
              onChange={(checked) => updateOption('ocr', checked)}
              disabled={disabled}
            />
            {options.ocr && (
              <>
                <div className="ml-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    엔진
                  </label>
                  <select
                    value={options.ocr_engine ?? 'paddle'}
                    onChange={(e) =>
                      updateOption('ocr_engine', e.target.value as 'paddle' | 'tesseract')
                    }
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                             disabled:opacity-50"
                  >
                    <option value="paddle">PaddleOCR (권장)</option>
                    <option value="tesseract">Tesseract</option>
                  </select>
                </div>
                <div className="ml-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    언어
                  </label>
                  <input
                    type="text"
                    value={options.ocr_langs ?? 'kor+eng'}
                    onChange={(e) => updateOption('ocr_langs', e.target.value)}
                    disabled={disabled}
                    placeholder="예: kor+eng"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                             disabled:opacity-50"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    한글+영문: kor+eng, 영문만: eng
                  </p>
                </div>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

interface CheckboxOptionProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function CheckboxOption({ label, checked, onChange, disabled }: CheckboxOptionProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500
                 disabled:opacity-50 cursor-pointer"
      />
      <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
    </label>
  );
}

