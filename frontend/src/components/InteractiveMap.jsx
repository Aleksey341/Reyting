import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Component to fit map bounds to markers
function FitBounds({ bounds }) {
  const map = useMap();

  React.useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);

  return null;
}

export default function InteractiveMap({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Нет данных для отображения</p>
      </div>
    );
  }

  // Filter data with valid coordinates
  const validData = data.filter(mo => mo.lat && mo.lon);

  if (validData.length === 0) {
    return (
      <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Нет координат для отображения на карте</p>
      </div>
    );
  }

  // Calculate bounds
  const bounds = validData.map(mo => [mo.lat, mo.lon]);

  // Get center (approximate center of Lipetsk Oblast)
  const center = [52.6, 39.6];

  const getMarkerColor = (zone) => {
    const colors = {
      green: '#2ecc71',
      yellow: '#f39c12',
      red: '#e74c3c',
    };
    return colors[zone] || '#95a5a6';
  };

  const getMarkerRadius = (score) => {
    // Scale radius based on score (5-15 pixels)
    return Math.max(5, Math.min(15, score / 10 + 5));
  };

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Зелёная зона',
      yellow: 'Жёлтая зона',
      red: 'Красная зона',
    };
    return labels[zone] || 'Нет данных';
  };

  return (
    <div className="h-96 rounded-lg overflow-hidden border border-gray-200">
      <MapContainer
        center={center}
        zoom={8}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitBounds bounds={bounds} />

        {validData.map((mo) => (
          <CircleMarker
            key={mo.mo_id}
            center={[mo.lat, mo.lon]}
            radius={getMarkerRadius(mo.score_total)}
            fillColor={getMarkerColor(mo.zone)}
            color="#fff"
            weight={2}
            opacity={1}
            fillOpacity={0.8}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-lg mb-2">{mo.mo_name}</h3>
                <div className="space-y-1 text-sm">
                  <p>
                    <span className="text-gray-600">Балл:</span>{' '}
                    <span className="font-semibold">{mo.score_total.toFixed(1)}</span>
                  </p>
                  <p>
                    <span className="text-gray-600">Зона:</span>{' '}
                    <span
                      className="font-semibold"
                      style={{ color: getMarkerColor(mo.zone) }}
                    >
                      {getZoneLabel(mo.zone)}
                    </span>
                  </p>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
