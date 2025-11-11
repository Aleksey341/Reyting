import React, { useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Component to fit map bounds
function FitBounds({ bounds }) {
  const map = useMap();

  React.useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);

  return null;
}

// Color scale based on score
const getColor = (value) => {
  if (value >= 80) return '#1a9850';  // Dark green
  if (value >= 60) return '#66bd63';  // Green
  if (value >= 40) return '#fee08b';  // Yellow
  if (value >= 20) return '#f46d43';  // Orange
  if (value >= 0) return '#d73027';   // Red
  return '#eeeeee';                   // Gray (no data)
};

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

export default function InteractiveMap({ data, onMunicipalityClick }) {
  // Convert data to GeoJSON FeatureCollection format
  const geoJsonData = useMemo(() => {
    if (!data || data.length === 0) return null;

    // Check if data already has geometry
    const validData = data.filter(mo => {
      // Check if has GeoJSON geometry
      if (mo.geojson && mo.geojson.geometry) {
        return true;
      }
      // Fallback: check if has lat/lon
      if (mo.lat && mo.lon) {
        return true;
      }
      return false;
    });

    if (validData.length === 0) return null;

    const features = validData.map(mo => {
      let geometry;

      // Use GeoJSON geometry if available
      if (mo.geojson && mo.geojson.geometry) {
        geometry = mo.geojson.geometry;
      } else if (mo.lat && mo.lon) {
        // Fallback: create a small polygon around the point
        const size = 0.15;
        const lat = mo.lat;
        const lon = mo.lon;

        geometry = {
          type: 'Polygon',
          coordinates: [[
            [lon - size, lat - size],
            [lon + size, lat - size],
            [lon + size, lat + size],
            [lon - size, lat + size],
            [lon - size, lat - size]
          ]]
        };
      }

      return {
        type: 'Feature',
        properties: {
          mo_id: mo.mo_id,
          name: mo.mo_name,
          score: mo.score_total || 0,
          zone: mo.zone,
        },
        geometry: geometry,
      };
    });

    return {
      type: 'FeatureCollection',
      features: features,
    };
  }, [data]);

  // Style function for GeoJSON
  const style = (feature) => {
    const score = feature.properties.score;
    const zone = feature.properties.zone;

    // If no zone or score is null/undefined, use gray color with low opacity (no data)
    if (!zone || score == null) {
      return {
        fillColor: '#e0e0e0',  // Light gray
        weight: 2,
        opacity: 0.5,
        color: '#9e9e9e',      // Gray border
        fillOpacity: 0.3,      // Very transparent
      };
    }

    return {
      fillColor: getZoneColor(zone),
      weight: 2,
      opacity: 0.8,
      color: '#2e7d32',
      fillOpacity: 0.6,
    };
  };

  // Event handlers for each feature
  const onEachFeature = (feature, layer) => {
    const { name, score, zone } = feature.properties;

    // Check if data exists
    const hasData = zone && score != null;
    const displayScore = hasData ? score.toFixed(1) : 'Нет данных';
    const displayZone = hasData ? `<span style="color: ${getZoneColor(zone)};">${getZoneLabel(zone)}</span>` : '<span style="color: #9e9e9e;">Нет данных</span>';

    // Popup content
    layer.bindPopup(`
      <div style="padding: 8px;">
        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${name}</h3>
        <div style="font-size: 14px; line-height: 1.6;">
          <p style="margin: 4px 0;"><strong>Балл:</strong> ${displayScore}</p>
          <p style="margin: 4px 0;"><strong>Зона:</strong> ${displayZone}</p>
        </div>
      </div>
    `);

    // Permanent label with municipality name
    layer.bindTooltip(name, {
      permanent: true,
      direction: 'center',
      className: 'municipality-label',
    });

    // Event handlers
    layer.on({
      mouseover: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 3,
          color: '#000',
          fillOpacity: 0.8,
        });
      },
      mouseout: (e) => {
        const layer = e.target;
        layer.setStyle(style(feature));
      },
      click: (e) => {
        // Call parent callback if provided
        if (onMunicipalityClick) {
          const moData = data.find(mo => mo.mo_name === name);
          if (moData) {
            onMunicipalityClick(moData);
          }
        }

        // Zoom to feature bounds
        e.target._map.fitBounds(e.target.getBounds(), {
          padding: [20, 20],
          maxZoom: 10
        });
      },
    });
  };

  // Calculate bounds for fitting
  const bounds = useMemo(() => {
    if (!geoJsonData || !geoJsonData.features.length) return null;

    const allCoords = [];
    geoJsonData.features.forEach(feature => {
      if (feature.geometry.type === 'Polygon') {
        feature.geometry.coordinates[0].forEach(coord => {
          allCoords.push([coord[1], coord[0]]);  // [lat, lon]
        });
      } else if (feature.geometry.type === 'MultiPolygon') {
        feature.geometry.coordinates.forEach(polygon => {
          polygon[0].forEach(coord => {
            allCoords.push([coord[1], coord[0]]);  // [lat, lon]
          });
        });
      }
    });

    return allCoords;
  }, [geoJsonData]);

  if (!geoJsonData) {
    return (
      <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Нет данных для отображения на карте</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="rounded-lg overflow-hidden border border-gray-200" style={{ height: '600px' }}>
        <style>{`
          .municipality-label {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            font-weight: 700 !important;
            color: #1f2937 !important;
            text-shadow:
              1px 1px 2px white,
              -1px -1px 2px white,
              1px -1px 2px white,
              -1px 1px 2px white,
              0 0 4px white !important;
            pointer-events: none !important;
            font-size: 12px !important;
          }
          .municipality-label::before {
            display: none !important;
          }
        `}</style>

        <MapContainer
          center={[52.6, 39.6]}
          zoom={8}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {bounds && <FitBounds bounds={bounds} />}

          <GeoJSON
            key={JSON.stringify(geoJsonData)}
            data={geoJsonData}
            style={style}
            onEachFeature={onEachFeature}
          />
        </MapContainer>
      </div>
    </div>
  );
}
