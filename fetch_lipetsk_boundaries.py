"""
Скрипт для получения реальных границ муниципалитетов Липецкой области из OpenStreetMap
"""
import requests
import json
import time

def fetch_lipetsk_boundaries():
    """Fetch real municipality boundaries for Lipetsk Oblast from Overpass API"""

    # Overpass API query для получения РЕАЛЬНОЙ геометрии (не bbox)
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Запрос для получения всех муниципальных районов Липецкой области с полной геометрией
    query = """
    [out:json][timeout:180];
    area["ISO3166-2"="RU-LIP"]->.a;
    (
      relation["boundary"="administrative"]["admin_level"="6"](area.a);
    );
    out geom;
    """

    print("Отправка запроса к Overpass API...")
    print(f"URL: {overpass_url}")

    try:
        response = requests.post(overpass_url, data={'data': query}, timeout=200)
        response.raise_for_status()

        data = response.json()
        print(f"Получено {len(data.get('elements', []))} объектов")

        # Конвертируем в GeoJSON FeatureCollection
        features = []

        for element in data.get('elements', []):
            if element.get('type') != 'relation':
                continue

            tags = element.get('tags', {})
            name = tags.get('name', '')

            if not name:
                continue

            # Строим геометрию из members
            geometry = build_geometry_from_members(element)

            if geometry:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "admin_level": tags.get('admin_level'),
                        "wikidata": tags.get('wikidata'),
                        "wikipedia": tags.get('wikipedia'),
                        "official_status": tags.get('official_status'),
                    },
                    "geometry": geometry
                }
                features.append(feature)
                print(f"[OK] Dobavlen: {name}")

        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }

        # Сохраняем в файл
        output_file = 'lipetsk_boundaries_real_full.geojson'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(feature_collection, f, ensure_ascii=False, indent=2)

        print(f"\n[SUCCESS] Sohraneno {len(features)} municipalitetov v {output_file}")
        return feature_collection

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Oshibka pri zaprose: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Oshibka: {e}")
        return None


def build_geometry_from_members(relation):
    """Build geometry from relation members with 'geometry' field"""
    members = relation.get('members', [])

    if not members:
        return None

    # Collect all ways (outer and inner rings)
    outer_ways = []
    inner_ways = []

    for member in members:
        if member.get('type') != 'way':
            continue

        role = member.get('role', '')
        geometry = member.get('geometry', [])

        if not geometry:
            continue

        # Convert to [lon, lat] format
        coords = [[point['lon'], point['lat']] for point in geometry]

        if role == 'outer':
            outer_ways.append(coords)
        elif role == 'inner':
            inner_ways.append(coords)

    if not outer_ways:
        return None

    # Merge connected ways into rings
    outer_rings = merge_ways(outer_ways)
    inner_rings = merge_ways(inner_ways)

    # Build Polygon or MultiPolygon
    if len(outer_rings) == 1:
        # Simple Polygon
        coordinates = [outer_rings[0]]
        if inner_rings:
            coordinates.extend(inner_rings)

        return {
            "type": "Polygon",
            "coordinates": coordinates
        }
    else:
        # MultiPolygon
        polygons = [[ring] for ring in outer_rings]

        return {
            "type": "MultiPolygon",
            "coordinates": polygons
        }


def merge_ways(ways):
    """Merge connected ways into closed rings"""
    if not ways:
        return []

    rings = []

    while ways:
        current_ring = ways.pop(0)

        # Try to extend current ring by connecting other ways
        changed = True
        while changed:
            changed = False
            for i, way in enumerate(ways):
                # Check if way connects to start or end of current ring
                if current_ring[-1] == way[0]:
                    current_ring.extend(way[1:])
                    ways.pop(i)
                    changed = True
                    break
                elif current_ring[-1] == way[-1]:
                    current_ring.extend(way[-2::-1])
                    ways.pop(i)
                    changed = True
                    break
                elif current_ring[0] == way[-1]:
                    current_ring = way[:-1] + current_ring
                    ways.pop(i)
                    changed = True
                    break
                elif current_ring[0] == way[0]:
                    current_ring = way[-1:0:-1] + current_ring
                    ways.pop(i)
                    changed = True
                    break

        # Close ring if needed
        if current_ring[0] != current_ring[-1]:
            current_ring.append(current_ring[0])

        rings.append(current_ring)

    return rings


if __name__ == "__main__":
    print("=" * 60)
    print("Получение реальных границ муниципалитетов Липецкой области")
    print("=" * 60)
    print()

    result = fetch_lipetsk_boundaries()

    if result:
        print("\n[SUCCESS] Gotovo! Teper zagruzite fayl cherez API:")
        print("   POST http://localhost:8000/api/import/upload-real-boundaries")
        print("   File: lipetsk_boundaries_real_full.geojson")
    else:
        print("\n[ERROR] Ne udalos poluchit granicy")
        print("\nAlternativa: ispolzuyte gotovyy fayl iz drugogo istochnika")
        print("Naprimer: https://github.com/datasets/geo-countries ili analogichnye repozitorii")
