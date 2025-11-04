import React, { useState, useEffect } from 'react';
import { indicatorService } from '../services/api';

export default function AnalyticsPage({ period }) {
  const [indicators, setIndicators] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterBlock, setFilterBlock] = useState(null);

  useEffect(() => {
    const fetchIndicators = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await indicatorService.getIndicators(filterBlock, true);
        setIndicators(response.data.data || []);
      } catch (err) {
        console.error('Error fetching indicators:', err);
        setError('Ошибка загрузки показателей');
      } finally {
        setLoading(false);
      }
    };

    fetchIndicators();
  }, [filterBlock]);

  const blocks = [
    { value: null, label: 'Все блоки' },
    { value: 'Полит. менеджмент', label: 'Политический менеджмент' },
    { value: 'Забота и внимание', label: 'Забота и внимание' },
    { value: 'Развитие кадрового потенциала', label: 'Кадровый потенциал' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка аналитики...</p>
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
        <h2 className="text-xl font-semibold mb-6">Аналитика показателей</h2>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Фильтр по блокам:
          </label>
          <div className="flex flex-wrap gap-2">
            {blocks.map((block) => (
              <button
                key={block.value || 'all'}
                onClick={() => setFilterBlock(block.value)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  filterBlock === block.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {block.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {indicators.map((indicator) => (
            <div
              key={indicator.ind_id}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-gray-900">{indicator.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">Код: {indicator.code}</p>
                </div>
                <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded">
                  {indicator.is_public ? 'Публичный' : 'Закрытый'}
                </span>
              </div>

              <div className="text-sm text-gray-600 mb-3">
                {indicator.block && (
                  <p className="text-xs text-gray-500">
                    Блок: <span className="font-medium">{indicator.block}</span>
                  </p>
                )}
                {indicator.owner_org && (
                  <p className="text-xs text-gray-500">
                    Ведомство: <span className="font-medium">{indicator.owner_org}</span>
                  </p>
                )}
                {indicator.unit && (
                  <p className="text-xs text-gray-500">
                    Единица: <span className="font-medium">{indicator.unit}</span>
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {indicators.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600">Показатели не найдены</p>
          </div>
        )}
      </div>
    </div>
  );
}
