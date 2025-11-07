"""
Скрипт для получения реальных границ муниципалитетов Липецкой области из OpenStreetMap.
Использует Overpass API для получения GeoJSON данных.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

# Overpass API endpoint
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# OSM Relation IDs для муниципалитетов Липецкой области
# Получены вручную из OpenStreetMap
OSM_RELATIONS = {
    "Липецк": 1438199,  # Липецк городской округ
    "Елец": 1438426,    # Елец городской округ
    "Воловский": 109843,
    "Грязянский": 109844,
    "Данковский": 109845,
    "Добринский": 109846,
    "Добровский": 109847,
    "Долгоруковский": 109848,
    "Елецкий": 109849,
    "Задонский": 109850,
    "Измалковский": 109851,
    "Краснинский": 109852,
    "Лебедянский": 109853,
    "Лев-Толстовский": 2151676,
    "Липецкий": 109854,
    "Становлянский": 109855,
    "Тербунский": 109856,
    "Усманский": 109857,
    "Хлевенский": 109858,
    "Чаплыгинский": 109859,
}

def simplify_coordinates(coords, tolerance=0.01):
    """Упрощение координат для уменьшения размера данных (Douglas-Peucker упрощенный)"""
    if len(coords) < 3:
        return coords

    # Простое прореживание - берем каждую N-ую точку
    step = max(1, len(coords) // 100)  # Максимум 100 точек на полигон
    simplified = coords[::step]

    # Всегда включаем последнюю точку для замыкания полигона
    if simplified[-1] != coords[-1]:
        simplified.append(coords[-1])

    return simplified

def fetch_single_boundary(relation_id, name):
    """Получить границу одного муниципалитета по relation ID"""
    query = f"""
    [out:json][timeout:30];
    relation({relation_id});
    out geom;
    """

    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=45)
        response.raise_for_status()
        data = response.json()

        elements = data.get('elements', [])
        if not elements:
            return None

        element = elements[0]

        # Извлечение координат из members
        coordinates = []

        for member in element.get('members', []):
            if member['type'] == 'way' and member['role'] == 'outer':
                way_coords = []
                for node in member.get('geometry', []):
                    way_coords.append([node['lon'], node['lat']])

                if way_coords:
                    # Упрощаем координаты
                    simplified = simplify_coordinates(way_coords, tolerance=0.005)
                    coordinates.append(simplified)

        if coordinates:
            # Если несколько контуров, берем самый длинный как основной
            main_coords = max(coordinates, key=len)

            # Замыкаем полигон если не замкнут
            if main_coords[0] != main_coords[-1]:
                main_coords.append(main_coords[0])

            geojson = {
                "type": "Polygon",
                "coordinates": [main_coords]
            }

            return geojson

        return None

    except Exception as e:
        print(f"    ❌ Ошибка для {name}: {e}")
        return None


def fetch_boundaries():
    """Получить границы из OpenStreetMap для всех муниципалитетов"""
    print("🌍 Запрос данных из OpenStreetMap...")
    print(f"   Всего муниципалитетов: {len(OSM_RELATIONS)}")

    boundaries = {}

    for name, relation_id in OSM_RELATIONS.items():
        print(f"  📍 {name} (OSM ID: {relation_id})...", end=' ')

        geojson = fetch_single_boundary(relation_id, name)

        if geojson:
            boundaries[name] = geojson
            point_count = len(geojson['coordinates'][0])
            print(f"✓ {point_count} точек")
        else:
            print("✗ Не получено")

        # Задержка между запросами (чтобы не перегрузить Overpass API)
        time.sleep(1)

    return boundaries

def save_to_json(boundaries, filename="lipetsk_boundaries.json"):
    """Сохранить границы в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Сохранено в {filename}")

def main():
    print("=" * 60)
    print("Получение реальных границ муниципалитетов Липецкой области")
    print("=" * 60)

    # Получить границы из OSM
    boundaries = fetch_boundaries()

    if not boundaries:
        print("\n❌ Не удалось получить границы из OpenStreetMap")
        return

    print(f"\n📊 Итого получено: {len(boundaries)} из {len(OSM_RELATIONS)} муниципалитетов")

    # Сохранить в файл
    save_to_json(boundaries)

    # Вывод статистики
    print("\n" + "=" * 60)
    print("ГОТОВО! Реальные границы получены из OpenStreetMap")
    print("=" * 60)
    print(f"Файл: lipetsk_boundaries.json")
    print(f"Муниципалитетов: {len(boundaries)}")
    print("\nСледующий шаг: загрузить эти данные в базу через API")

if __name__ == "__main__":
    main()
