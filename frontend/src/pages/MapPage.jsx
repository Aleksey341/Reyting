import React, { useState, useEffect } from 'react';
import { mapService } from '../services/api';
import InteractiveMap from '../components/InteractiveMap';

export default function MapPage({ period }) {
  const [mapData, setMapData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMO, setSelectedMO] = useState(null);

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
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">{selectedMO.mo_name}</h3>
            <button
              onClick={() => setSelectedMO(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Итоговый балл</p>
              <p className="text-3xl font-bold text-gray-900">
                {selectedMO.score_total != null ? selectedMO.score_total.toFixed(1) : 'Нет данных'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Зона</p>
              <div
                className="inline-block px-3 py-1 rounded text-white font-semibold text-sm"
                style={{ backgroundColor: getZoneColor(selectedMO.zone) }}
              >
                {getZoneLabel(selectedMO.zone)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
