import React from 'react';
import { MapContainer, TileLayer, Polygon, Tooltip, Popup, useMap } from 'react-leaflet';
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

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Зелёная зона',
      yellow: 'Жёлтая зона',
      red: 'Красная зона',
    };
    return labels[zone] || 'Нет данных';
  };

  // Generate approximate boundary polygon around center point
  // This creates a rectangle - можно заменить на реальные границы из GeoJSON
  const generateBoundary = (lat, lon, size = 0.15) => {
    return [
      [lat + size, lon - size],
      [lat + size, lon + size],
      [lat - size, lon + size],
      [lat - size, lon - size],
    ];
  };

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200" style={{ height: '600px' }}>
      <style>{`
        .municipality-label {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          font-weight: 600 !important;
          color: #1f2937 !important;
          text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white !important;
        }
        .municipality-label::before {
          display: none !important;
        }
      `}</style>
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

        {validData.map((mo) => {
          const boundary = generateBoundary(mo.lat, mo.lon);
          const fillColor = getMarkerColor(mo.zone);

          return (
            <Polygon
              key={mo.mo_id}
              positions={boundary}
              pathOptions={{
                fillColor: fillColor,
                fillOpacity: 0.5,
                color: fillColor,
                weight: 2,
                opacity: 0.8,
              }}
              eventHandlers={{
                mouseover: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    fillOpacity: 0.7,
                    weight: 3,
                  });
                },
                mouseout: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    fillOpacity: 0.5,
                    weight: 2,
                  });
                },
              }}
            >
              {/* Permanent label with municipality name */}
              <Tooltip
                permanent
                direction="center"
                className="municipality-label"
                opacity={1}
              >
                <div className="text-sm font-semibold text-gray-800">
                  {mo.mo_name}
                </div>
              </Tooltip>

              {/* Popup on click */}
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
                        style={{ color: fillColor }}
                      >
                        {getZoneLabel(mo.zone)}
                      </span>
                    </p>
                  </div>
                </div>
              </Popup>
            </Polygon>
          );
        })}
      </MapContainer>
    </div>
  );
}
