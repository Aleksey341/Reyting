import React, { useState } from 'react';
import axios from 'axios';

export default function DataImportPage() {
  const [files, setFiles] = useState([]);
  const [period, setPeriod] = useState('2024-01');
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [importType, setImportType] = useState('official'); // 'official' or 'csv'

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      // Add new files to existing list
      const newFiles = selectedFiles.map((file, index) => ({
        id: Date.now() + index,
        file: file,
        name: file.name,
        size: file.size,
        status: 'pending', // pending, uploading, success, error
        progress: 0,
        result: null,
        error: null,
      }));
      setFiles((prev) => [...prev, ...newFiles]);
      // Reset results when new files are added
      setUploadResults([]);
    }
  };

  const removeFile = (fileId) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const uploadFile = async (fileItem) => {
    const formData = new FormData();
    formData.append('file', fileItem.file);

    const apiUrl = import.meta.env.VITE_API_URL || '/api';

    // Choose endpoint based on import type
    const endpoint = importType === 'official'
      ? `${apiUrl}/import/official-methodology?period_month=${period}`
      : `${apiUrl}/import/csv?period_month=${period}`;

    try {
      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileItem.id
                ? { ...f, progress: percentCompleted }
                : f
            )
          );
        },
      });

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Upload error:', err);
      return {
        success: false,
        error: err.response?.data?.detail || 'Ошибка при загрузке файла',
      };
    }
  };

  const handleUploadAll = async () => {
    if (files.length === 0) {
      return;
    }

    setUploading(true);
    setUploadResults([]);

    // Mark all files as uploading
    setFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading', progress: 0 }))
    );

    const results = [];

    // Upload files sequentially
    for (const fileItem of files) {
      const result = await uploadFile(fileItem);

      if (result.success) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileItem.id
              ? {
                  ...f,
                  status: 'success',
                  progress: 100,
                  result: result.data,
                }
              : f
          )
        );
        results.push({
          fileName: fileItem.name,
          success: true,
          data: result.data,
        });
      } else {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileItem.id
              ? {
                  ...f,
                  status: 'error',
                  error: result.error,
                }
              : f
          )
        );
        results.push({
          fileName: fileItem.name,
          success: false,
          error: result.error,
        });
      }
    }

    setUploadResults(results);
    setUploading(false);
  };

  const clearAll = () => {
    setFiles([]);
    setUploadResults([]);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
          </svg>
        );
      case 'uploading':
        return (
          <svg className="animate-spin h-5 w-5 text-blue-500" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        );
      case 'success':
        return (
          <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Загрузка данных из CSV
        </h2>

        <div className="space-y-6">
          {/* Import type selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип импорта
            </label>
            <div className="flex gap-6">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="official"
                  checked={importType === 'official'}
                  onChange={(e) => setImportType(e.target.value)}
                  disabled={uploading}
                  className="w-4 h-4 mr-2"
                />
                <span className="text-sm text-gray-700">
                  Официальная методология (16 критериев)
                </span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="csv"
                  checked={importType === 'csv'}
                  onChange={(e) => setImportType(e.target.value)}
                  disabled={uploading}
                  className="w-4 h-4 mr-2"
                />
                <span className="text-sm text-gray-700">
                  Пользовательские показатели
                </span>
              </label>
            </div>
            <p className="mt-2 text-sm text-gray-500">
              {importType === 'official'
                ? 'Загрузите CSV с данными по 16 официальным критериям. Баллы будут автоматически рассчитаны.'
                : 'Загрузите CSV с пользовательскими показателями (старый формат).'}
            </p>
          </div>

          {/* Period selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Период данных
            </label>
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              disabled={uploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <p className="mt-1 text-sm text-gray-500">
              Выберите месяц, к которому относятся данные во всех CSV файлах
            </p>
          </div>

          {/* File selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CSV файлы
            </label>
            <input
              type="file"
              accept=".csv"
              multiple
              onChange={handleFileChange}
              disabled={uploading}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                disabled:opacity-50 disabled:cursor-not-allowed
                cursor-pointer"
            />
            <p className="mt-1 text-sm text-gray-500">
              Можно выбрать несколько файлов. Формат: CSV с колонками "Муниципалитет" и показателями
            </p>
          </div>

          {/* Files list */}
          {files.length > 0 && (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-700">
                  Выбрано файлов: {files.length}
                </h3>
                {!uploading && (
                  <button
                    onClick={clearAll}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Очистить все
                  </button>
                )}
              </div>

              <ul className="divide-y divide-gray-200">
                {files.map((fileItem) => (
                  <li key={fileItem.id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1 min-w-0">
                        <div className="flex-shrink-0">
                          {getStatusIcon(fileItem.status)}
                        </div>
                        <div className="ml-3 flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {fileItem.name}
                          </p>
                          <div className="flex items-center gap-3 mt-1">
                            <p className="text-xs text-gray-500">
                              {formatFileSize(fileItem.size)}
                            </p>
                            {fileItem.status === 'uploading' && (
                              <p className="text-xs text-blue-600">
                                {fileItem.progress}%
                              </p>
                            )}
                            {fileItem.status === 'success' && fileItem.result && (
                              <p className="text-xs text-green-600">
                                Загружено {fileItem.result.statistics?.values_loaded || 0} значений
                              </p>
                            )}
                            {fileItem.status === 'error' && (
                              <p className="text-xs text-red-600">
                                {fileItem.error}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      {!uploading && fileItem.status === 'pending' && (
                        <button
                          onClick={() => removeFile(fileItem.id)}
                          className="ml-4 text-gray-400 hover:text-red-600"
                        >
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Progress bar */}
                    {fileItem.status === 'uploading' && (
                      <div className="mt-2 bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${fileItem.progress}%` }}
                        />
                      </div>
                    )}

                    {/* Success details */}
                    {fileItem.status === 'success' && fileItem.result?.statistics && (
                      <div className="mt-3 grid grid-cols-5 gap-2">
                        <div className="bg-green-50 rounded p-2 text-center">
                          <p className="text-xs text-gray-600">Строк</p>
                          <p className="text-sm font-bold text-gray-900">
                            {fileItem.result.statistics.rows}
                          </p>
                        </div>
                        <div className="bg-green-50 rounded p-2 text-center">
                          <p className="text-xs text-gray-600">Колонок</p>
                          <p className="text-sm font-bold text-gray-900">
                            {fileItem.result.statistics.columns}
                          </p>
                        </div>
                        <div className="bg-green-50 rounded p-2 text-center">
                          <p className="text-xs text-gray-600">МО</p>
                          <p className="text-sm font-bold text-gray-900">
                            {fileItem.result.statistics.municipalities_created}
                          </p>
                        </div>
                        <div className="bg-green-50 rounded p-2 text-center">
                          <p className="text-xs text-gray-600">Показателей</p>
                          <p className="text-sm font-bold text-gray-900">
                            {fileItem.result.statistics.indicators_created}
                          </p>
                        </div>
                        <div className="bg-green-50 rounded p-2 text-center">
                          <p className="text-xs text-gray-600">Значений</p>
                          <p className="text-sm font-bold text-gray-900">
                            {fileItem.result.statistics.values_loaded}
                          </p>
                        </div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Upload button */}
          <div>
            <button
              onClick={handleUploadAll}
              disabled={files.length === 0 || uploading}
              className={`w-full py-3 px-4 rounded-md font-semibold text-white transition-colors
                ${files.length === 0 || uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
                }`}
            >
              {uploading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Загрузка файлов...
                </span>
              ) : (
                `Загрузить все файлы (${files.length})`
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Summary after upload */}
      {uploadResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Результаты загрузки
          </h3>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Всего файлов</p>
              <p className="text-3xl font-bold text-gray-900">{uploadResults.length}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Успешно</p>
              <p className="text-3xl font-bold text-green-600">
                {uploadResults.filter((r) => r.success).length}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Ошибок</p>
              <p className="text-3xl font-bold text-red-600">
                {uploadResults.filter((r) => !r.success).length}
              </p>
            </div>
          </div>

          {/* Next steps */}
          {uploadResults.some((r) => r.success) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-800 mb-2">Следующие шаги:</p>
              <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
                <li>Обновите координаты МО (если нужно): POST /api/import/update-coordinates</li>
                <li>Пересчитайте баллы: POST /api/import/calculate-scores</li>
                <li>Проверьте данные на вкладке "Карта" или "Рейтинг"</li>
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Инструкция</h3>
        <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
          <li>Выберите период, к которому относятся данные (например, "2024-01" для января 2024)</li>
          <li>Выберите один или несколько CSV файлов с данными показателей</li>
          <li>Проверьте список выбранных файлов, удалите ненужные если требуется</li>
          <li>Нажмите "Загрузить все файлы" для начала загрузки</li>
          <li>Следите за прогрессом загрузки каждого файла</li>
          <li>После успешной загрузки данные будут доступны на карте и в рейтинге</li>
        </ol>
      </div>
    </div>
  );
}
