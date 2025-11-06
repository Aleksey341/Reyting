import React, { useState } from 'react';
import axios from 'axios';

export default function DataImportPage() {
  const [file, setFile] = useState(null);
  const [period, setPeriod] = useState('2024-01');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Выберите файл для загрузки');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Send request with period parameter
      const apiUrl = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.post(
        `${apiUrl}/import/csv?period_month=${period}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResult(response.data);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Ошибка при загрузке файла');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Загрузка данных из CSV
        </h2>

        <div className="space-y-6">
          {/* Period selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Период данных
            </label>
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Выберите месяц, к которому относятся данные в CSV файле
            </p>
          </div>

          {/* File selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CSV файл
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                cursor-pointer"
            />
            <p className="mt-1 text-sm text-gray-500">
              Формат: CSV с колонками "Муниципалитет" и показателями
            </p>
          </div>

          {/* Upload button */}
          <div>
            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className={`w-full py-3 px-4 rounded-md font-semibold text-white transition-colors
                ${!file || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
                }`}
            >
              {loading ? (
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
                  Загрузка...
                </span>
              ) : (
                'Загрузить данные'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Ошибка</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success message with statistics */}
      {result && result.status === 'success' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-start mb-4">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Успешно загружено</h3>
              <p className="mt-1 text-sm text-green-700">{result.message}</p>
            </div>
          </div>

          {/* Statistics */}
          {result.statistics && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <p className="text-sm text-gray-600">Строк в CSV</p>
                <p className="text-2xl font-bold text-gray-900">{result.statistics.rows}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <p className="text-sm text-gray-600">Колонок</p>
                <p className="text-2xl font-bold text-gray-900">{result.statistics.columns}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <p className="text-sm text-gray-600">МО создано</p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.statistics.municipalities_created}
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <p className="text-sm text-gray-600">Показателей создано</p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.statistics.indicators_created}
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-green-200">
                <p className="text-sm text-gray-600">Значений загружено</p>
                <p className="text-2xl font-bold text-gray-900">
                  {result.statistics.values_loaded}
                </p>
              </div>
            </div>
          )}

          {/* Next steps */}
          <div className="mt-6 pt-4 border-t border-green-200">
            <p className="text-sm font-medium text-green-800 mb-2">Следующие шаги:</p>
            <ol className="list-decimal list-inside text-sm text-green-700 space-y-1">
              <li>Обновите координаты МО (если нужно): POST /api/import/update-coordinates</li>
              <li>Пересчитайте баллы: POST /api/import/calculate-scores</li>
              <li>Проверьте данные на вкладке "Карта" или "Рейтинг"</li>
            </ol>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Инструкция</h3>
        <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
          <li>Выберите период, к которому относятся данные (например, "2024-01" для января 2024)</li>
          <li>Выберите CSV файл с данными показателей</li>
          <li>Нажмите "Загрузить данные"</li>
          <li>После успешной загрузки данные будут доступны на карте и в рейтинге для выбранного периода</li>
        </ol>
      </div>
    </div>
  );
}
