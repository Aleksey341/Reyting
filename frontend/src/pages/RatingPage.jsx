import React, { useState, useEffect } from 'react';
import { ratingService } from '../services/api';

export default function RatingPage({ period }) {
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sort, setSort] = useState('score_total');
  const [showZoneModal, setShowZoneModal] = useState(false);
  const pageSize = 50;

  // Предопределенные параметры (столбцы для баллов)
  const parameterColumns = [
    { code: '1', label: '1' },
    { code: '2', label: '2' },
    { code: '3', label: '3' },
    { code: '4', label: '4' },
    { code: '5', label: '5' },
    { code: '6', label: '6' },
    { code: '7', label: '7' },
    { code: '8', label: '8' },
    { code: '9', label: '9' },
    { code: '10', label: '10' },
    { code: '11', label: '11' },
    { code: '12', label: '12' },
    { code: '13', label: '13' },
    { code: '14', label: '14' },
    { code: '15', label: '15' },
    { code: '16', label: '16' },
    { code: '17', label: '17' },
  ];

  const penaltyColumns = [
    { code: 'penalty_18', label: '18' },
    { code: 'penalty_19', label: '19' },
    { code: 'penalty_20', label: '20' },
    { code: 'penalty_21', label: '21' },
  ];

  useEffect(() => {
    const fetchRating = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await ratingService.getRating(period, null, sort, currentPage, pageSize);
        setRatingData(response.data.data || []);
      } catch (err) {
        console.error('Error fetching rating:', err);
        setError('Ошибка загрузки рейтинга');
      } finally {
        setLoading(false);
      }
    };

    fetchRating();
  }, [period, sort, currentPage]);

  const getScoreColor = (score) => {
    if (score >= 53) return '#2ecc71'; // Зеленая
    if (score >= 29) return '#f39c12'; // Желтая
    return '#e74c3c'; // Красная
  };

  const getScoreTextColor = (score) => {
    if (score >= 53) return '#27ae60'; // Темно-зеленый
    if (score >= 29) return '#d68910'; // Темно-оранжевый
    return '#c0392b'; // Темно-красный
  };

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Зелёная',
      yellow: 'Жёлтая',
      red: 'Красная',
    };
    return labels[zone] || 'Нет данных';
  };

  const getIndicatorScore = (item, code) => {
    return item.indicators && item.indicators[code] !== undefined
      ? item.indicators[code]
      : 0;
  };

  const getPenaltyScore = (item, code) => {
    return item.penalties && item.penalties[code] !== undefined
      ? item.penalties[code]
      : 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка рейтинга...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Рейтинг муниципальных образований</h2>
          <button
            onClick={() => setShowZoneModal(true)}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md text-sm hover:bg-blue-200"
          >
            ℹ️ Описание зон
          </button>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <label className="text-sm font-medium text-gray-700">Сортировать по:</label>
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="score_total">Итоговый балл</option>
            <option value="score_public">Публичный рейтинг</option>
            <option value="mo_name">Название МО</option>
          </select>
        </div>

        {/* Таблица с горизонтальной прокруткой */}
        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b sticky top-0">
              <tr>
                {/* Зафиксированные колонки */}
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[40px]">
                  №
                </th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[180px]">
                  Главы муниципалитетов
                </th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[150px]">
                  ФИО главы
                </th>

                {/* Заголовок для раздела "Баллы за критерии" */}
                <th
                  colSpan={parameterColumns.length}
                  className="px-3 py-3 text-center font-semibold text-gray-700 bg-blue-50 border-l border-r border-gray-300"
                >
                  Баллы за критерии
                </th>

                {/* Заголовок для раздела "Штрафы" */}
                <th
                  colSpan={penaltyColumns.length}
                  className="px-3 py-3 text-center font-semibold text-gray-700 bg-red-50 border-l border-r border-gray-300"
                >
                  Штрафы
                </th>

                {/* Итоговый балл */}
                <th className="px-3 py-3 text-center font-semibold text-gray-700 bg-green-50 min-w-[80px]">
                  ИТОГ
                </th>
              </tr>

              {/* Второй ряд заголовка - номера критериев */}
              <tr>
                <th colSpan="3" className="px-3 py-2 bg-gray-50"></th>
                {parameterColumns.map((col) => (
                  <th
                    key={col.code}
                    className="px-2 py-2 text-center font-medium text-gray-600 bg-blue-50 border-r border-gray-200 text-xs"
                  >
                    {col.label}
                  </th>
                ))}
                {penaltyColumns.map((col) => (
                  <th
                    key={col.code}
                    className="px-2 py-2 text-center font-medium text-gray-600 bg-red-50 border-r border-gray-200 text-xs"
                  >
                    {col.label}
                  </th>
                ))}
                <th className="px-3 py-2 bg-green-50"></th>
              </tr>
            </thead>

            <tbody>
              {ratingData.map((item, index) => (
                <tr key={item.mo_id} className="border-b hover:bg-gray-50">
                  {/* Номер */}
                  <td className="px-3 py-3 font-semibold text-gray-900 bg-white min-w-[40px]">
                    {(currentPage - 1) * pageSize + index + 1}
                  </td>

                  {/* Название МО */}
                  <td className="px-3 py-3 text-gray-900 font-medium bg-white min-w-[180px]">
                    {item.mo_name}
                  </td>

                  {/* ФИО главы */}
                  <td className="px-3 py-3 text-gray-700 bg-white min-w-[150px]">
                    {item.leader_name}
                  </td>

                  {/* Баллы за критерии */}
                  {parameterColumns.map((col) => (
                    <td
                      key={col.code}
                      className="px-2 py-3 text-center text-gray-600 border-r border-gray-200 bg-blue-50 text-sm"
                    >
                      {getIndicatorScore(item, col.code)}
                    </td>
                  ))}

                  {/* Штрафы */}
                  {penaltyColumns.map((col) => (
                    <td
                      key={col.code}
                      className="px-2 py-3 text-center text-red-600 border-r border-gray-200 bg-red-50 text-sm font-medium"
                    >
                      {getPenaltyScore(item, col.code)}
                    </td>
                  ))}

                  {/* Итоговый балл с цветовой дифференциацией */}
                  <td className="px-3 py-3 text-center font-bold min-w-[80px] bg-white">
                    <span
                      style={{
                        color: getScoreTextColor(item.score_total),
                        fontSize: '16px',
                        fontWeight: 'bold',
                      }}
                    >
                      {item.score_total.toFixed(0)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Пагинация */}
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Показано {ratingData.length} МО
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 border rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              ← Назад
            </button>
            <button
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={ratingData.length < pageSize}
              className="px-3 py-2 border rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Далее →
            </button>
          </div>
        </div>
      </div>

      {/* Модальное окно с описанием зон */}
      {showZoneModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Описание зон</h3>
              <button
                onClick={() => setShowZoneModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Зелёная зона */}
              <div className="border-l-4 border-green-500 pl-4 py-3 bg-green-50 rounded">
                <h4 className="font-bold text-green-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-green-500 rounded"></span>
                  Зелёная зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">53-66 баллов</p>
                <p className="text-gray-700">
                  <strong>Высокая устойчивость</strong> – Отставка маловероятна, глава МО обладает значительным ресурсом для управления и карьерного роста
                </p>
              </div>

              {/* Жёлтая зона */}
              <div className="border-l-4 border-yellow-500 pl-4 py-3 bg-yellow-50 rounded">
                <h4 className="font-bold text-yellow-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-yellow-500 rounded"></span>
                  Жёлтая зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">29-52 баллов</p>
                <p className="text-gray-700">
                  <strong>Условная устойчивость</strong> – Существуют риски, требующие коррекции управленческой или политической стратегии
                </p>
              </div>

              {/* Красная зона */}
              <div className="border-l-4 border-red-500 pl-4 py-3 bg-red-50 rounded">
                <h4 className="font-bold text-red-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-red-500 rounded"></span>
                  Красная зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">0-28 баллов</p>
                <p className="text-gray-700">
                  <strong>Низкая устойчивость</strong> – Высокий риск отставки в среднесрочной перспективе, наличие серьёзных системных проблем
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowZoneModal(false)}
              className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
