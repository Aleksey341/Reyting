import React, { useState, useEffect } from 'react';
import { mapService } from '../services/api';
import InteractiveMap from '../components/InteractiveMap';

export default function MapPage({ period }) {
  const [mapData, setMapData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMO, setSelectedMO] = useState(null);
  const [activeTab, setActiveTab] = useState('rating'); // 'rating' или 'penalties'

  useEffect(() => {
    const fetchMapData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await mapService.getMapData(period);
        setMapData(response.data.data || []);
      } catch (err) {
        console.error('Error fetching map data:', err);
        setError('Ошибка загрузки данных карты');
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, [period]);

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
      green: 'Зелёная зона',
      yellow: 'Жёлтая зона',
      red: 'Красная зона',
    };
    return labels[zone] || 'Нет данных';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка данных...</p>
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

  // Group by zones (exclude municipalities with no data)
  const zones = {
    green: mapData.filter(d => d.zone === 'green' && d.score_total != null),
    yellow: mapData.filter(d => d.zone === 'yellow' && d.score_total != null),
    red: mapData.filter(d => d.zone === 'red' && d.score_total != null),
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Карта МО Липецкой области</h2>

        {/* Interactive Map */}
        <InteractiveMap data={mapData} onMunicipalityClick={setSelectedMO} />
      </div>

      {selectedMO && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-bold">{selectedMO.mo_name}</h3>
              <button
                onClick={() => {
                  setSelectedMO(null);
                  setActiveTab('rating');
                }}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
              >
                ✕
              </button>
            </div>

            {/* Summary stats */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-blue-100 text-sm">Итоговый балл</p>
                <p className="text-3xl font-bold">
                  {selectedMO.score_total != null ? selectedMO.score_total.toFixed(1) : '—'}
                </p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Статус</p>
                <div
                  className="inline-block px-3 py-1 rounded text-white font-semibold text-sm"
                  style={{ backgroundColor: getZoneColor(selectedMO.zone) }}
                >
                  {getZoneLabel(selectedMO.zone)}
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 bg-gray-50">
            <button
              onClick={() => setActiveTab('rating')}
              className={`flex-1 py-4 px-4 font-semibold text-center transition ${
                activeTab === 'rating'
                  ? 'border-b-2 border-blue-600 text-blue-600 bg-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📊 Основной рейтинг
            </button>
            <button
              onClick={() => setActiveTab('penalties')}
              className={`flex-1 py-4 px-4 font-semibold text-center transition ${
                activeTab === 'penalties'
                  ? 'border-b-2 border-red-600 text-red-600 bg-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              ⚠️ Штрафные баллы
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'rating' && (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Публичный рейтинг</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {selectedMO.score_public != null ? selectedMO.score_public.toFixed(1) : '—'}
                  </p>
                  <p className="text-xs text-gray-500">макс. 31 балл</p>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Закрытый рейтинг</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {selectedMO.score_closed != null ? selectedMO.score_closed.toFixed(1) : '—'}
                  </p>
                  <p className="text-xs text-gray-500">макс. 35 баллов</p>
                </div>

                <div className="mt-6">
                  <h4 className="font-semibold text-gray-900 mb-3">Основные показатели:</h4>
                  <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map((num) => (
                      <div key={num} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-gray-700">Показатель {num}</span>
                        <span className="font-semibold text-gray-900">
                          {selectedMO[`pub_${num}`] || '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'penalties' && (
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Штрафные баллы</p>
                  <p className="text-2xl font-bold text-red-600">
                    {selectedMO.score_penalties != null ? selectedMO.score_penalties.toFixed(1) : '0'}
                  </p>
                  <p className="text-xs text-gray-500">макс. -10 баллов</p>
                </div>

                <div className="mt-6">
                  <h4 className="font-semibold text-gray-900 mb-3">Штрафные критерии:</h4>
                  <div className="space-y-3">
                    <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-900">П1. Конфликты с региональной властью</span>
                        <span className="text-red-600 font-bold">
                          {selectedMO.pen_1 != null ? selectedMO.pen_1.toFixed(1) : '—'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">макс. -3 балла</p>
                    </div>

                    <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-900">П2. Внутримуниципальные конфликты</span>
                        <span className="text-red-600 font-bold">
                          {selectedMO.pen_2 != null ? selectedMO.pen_2.toFixed(1) : '—'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">макс. -3 балла</p>
                    </div>

                    <div className="p-3 border border-red-200 rounded-lg bg-red-50">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-900">П3. Правоохранительные органы</span>
                        <span className="text-red-600 font-bold">
                          {selectedMO.pen_3 != null ? selectedMO.pen_3.toFixed(1) : '—'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">макс. -5 баллов</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
