import React, { useState, useEffect } from 'react';
import { ratingService } from '../services/api';

export default function RatingPage({ period }) {
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sort, setSort] = useState('score_total');
  const pageSize = 50;

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

  const getZoneColor = (zone) => {
    const colors = {
      green: '#2ecc71',
      yellow: '#f39c12',
      red: '#e74c3c',
    };
    return colors[zone] || '#95a5a6';
  };

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Зелёная',
      yellow: 'Жёлтая',
      red: 'Красная',
    };
    return labels[zone] || 'Нет данных';
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
        <h2 className="text-xl font-semibold mb-6">Рейтинг МО</h2>

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

        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-700">Ранг</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-700">МО</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Публичный</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Закрытый</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Штрафы</th>
                <th className="px-6 py-3 text-right font-semibold text-gray-700">Итого</th>
                <th className="px-6 py-3 text-center font-semibold text-gray-700">Зона</th>
              </tr>
            </thead>
            <tbody>
              {ratingData.map((item, index) => (
                <tr key={item.mo_id} className="border-b hover:bg-gray-50">
                  <td className="px-6 py-3 font-semibold text-gray-900">
                    {(currentPage - 1) * pageSize + index + 1}
                  </td>
                  <td className="px-6 py-3 text-gray-900 font-medium">{item.mo_name}</td>
                  <td className="px-6 py-3 text-right text-gray-600">
                    {item.score_public.toFixed(1)}
                  </td>
                  <td className="px-6 py-3 text-right text-gray-600">
                    {item.score_closed.toFixed(1)}
                  </td>
                  <td className="px-6 py-3 text-right text-red-600 font-medium">
                    {item.score_penalties.toFixed(1)}
                  </td>
                  <td className="px-6 py-3 text-right font-semibold text-gray-900">
                    {item.score_total.toFixed(1)}
                  </td>
                  <td className="px-6 py-3 text-center">
                    <span
                      className="px-2 py-1 rounded text-white text-xs font-semibold"
                      style={{ backgroundColor: getZoneColor(item.zone) }}
                    >
                      {getZoneLabel(item.zone)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

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
    </div>
  );
}
