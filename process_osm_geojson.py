"""
Обработка GeoJSON файла из Overpass Turbo.
Упрощает границы и сопоставляет с муниципалитетами в БД.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json

# Список муниципалитетов из БД
DB_MUNICIPALITIES = {
    "Липецк": ["Липецк", "Lipetsk"],
    "Елец": ["Елец", "Elets"],
    "Воловский": ["Воловский", "Volovskiy"],
    "Грязянский": ["Грязинский", "Грязянский", "Gryazinskiy"],
    "Данковский": ["Данковский", "Dankovskiy"],
    "Добринский": ["Добринский", "Dobrinskiy"],
    "Добровский": ["Добровский", "Dobrovskiy"],
    "Долгоруковский": ["Долгоруковский", "Dolgorukovskiy"],
    "Елецкий": ["Елецкий", "Eletskiy"],
    "Задонский": ["Задонский", "Zadonskiy"],
    "Измалковский": ["Измалковский", "Izmalkovskiy"],
    "Краснинский": ["Краснинский", "Krasninskiy"],
    "Лебедянский": ["Лебедянский", "Lebedyanskiy"],
    "Лев-Толстовский": ["Лев-Толстовский", "Lev-Tolstovskiy"],
    "Липецкий": ["Липецкий", "Lipetskiy"],
    "Становлянский": ["Становлянский", "Stanovlyanskiy"],
    "Тербунский": ["Тербунский", "Terbunskiy"],
    "Усманский": ["Усманский", "Usmanskiy"],
    "Хлевенский": ["Хлевенский", "Khlevenskiy"],
    "Чаплыгинский": ["Чаплыгинский", "Chaplyginskiy"],
}

def simplify_coordinates(coords, tolerance=0.01):
    """Упрощение координат - берем каждую N-ую точку"""
    if len(coords) < 10:
        return coords

    # Оставляем каждую 5-ую точку (уменьшаем детализацию)
    step = max(1, len(coords) // 50)  # Максимум 50 точек
    simplified = coords[::step]

    # Всегда включаем последнюю точку
    if simplified[-1] != coords[-1]:
        simplified.append(coords[-1])

    return simplified

def normalize_name(name):
    """Нормализация названия для сопоставления"""
    return (name.lower()
            .replace(' район', '')
            .replace(' муниципальный район', '')
            .replace(' городской округ', '')
            .replace('город ', '')
            .replace('г. ', '')
            .replace('г.', '')
            .replace('«', '')
            .replace('»', '')
            .replace('"', '')
            .strip())

def match_municipality_name(osm_name):
    """Сопоставление названия из OSM с названием в БД"""
    osm_norm = normalize_name(osm_name)

    # Прямое совпадение
    for db_name, variants in DB_MUNICIPALITIES.items():
        db_norm = normalize_name(db_name)
        if osm_norm == db_norm:
            return db_name

        # Проверка вариантов
        for variant in variants:
            var_norm = normalize_name(variant)
            if osm_norm == var_norm or osm_norm in var_norm or var_norm in osm_norm:
                return db_name

    # Проверка по началу названия
    for db_name, variants in DB_MUNICIPALITIES.items():
        db_norm = normalize_name(db_name)
        if len(osm_norm) >= 3 and len(db_norm) >= 3:
            if osm_norm.startswith(db_norm[:3]) or db_norm.startswith(osm_norm[:3]):
                return db_name

    return None

def process_geojson(input_file="lipetsk_osm.geojson", output_file="lipetsk_boundaries_real.json"):
    """Обработать GeoJSON файл из Overpass Turbo"""
    print("=" * 60)
    print("Обработка GeoJSON из OpenStreetMap")
    print("=" * 60)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {input_file} не найден!")
        print(f"   Скачайте GeoJSON из Overpass Turbo и сохраните как {input_file}")
        return

    print(f"✓ Загружен файл: {input_file}")

    boundaries = {}
    features = data.get('features', [])

    print(f"  Найдено объектов: {len(features)}")
    print()

    for feature in features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})

        # Получаем название (приоритет name:ru, затем name)
        osm_name = properties.get('name:ru') or properties.get('name', '')
        if not osm_name:
            continue

        # Сопоставляем с БД
        db_name = match_municipality_name(osm_name)
        if not db_name:
            print(f"  ⚠ Не найдено: {osm_name}")
            continue

        print(f"  ✓ {osm_name:30s} → {db_name}")

        # Обрабатываем геометрию
        geom_type = geometry.get('type')

        if geom_type == 'Polygon':
            coords = geometry['coordinates'][0]
            simplified = simplify_coordinates(coords)

            boundaries[db_name] = {
                "type": "Polygon",
                "coordinates": [simplified]
            }
            print(f"     {len(coords)} → {len(simplified)} точек")

        elif geom_type == 'MultiPolygon':
            # Берем самый большой полигон
            all_polygons = geometry['coordinates']
            largest = max(all_polygons, key=lambda p: len(p[0]))
            coords = largest[0]
            simplified = simplify_coordinates(coords)

            boundaries[db_name] = {
                "type": "Polygon",
                "coordinates": [simplified]
            }
            print(f"     MultiPolygon: {len(coords)} → {len(simplified)} точек")

    print(f"\n📊 Обработано: {len(boundaries)} из {len(DB_MUNICIPALITIES)} муниципалитетов")

    # Сохранить
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)

    print(f"💾 Сохранено: {output_file}")

    # Показать какие не найдены
    missing = set(DB_MUNICIPALITIES.keys()) - set(boundaries.keys())
    if missing:
        print(f"\n⚠ Не найдены в OSM:")
        for name in sorted(missing):
            print(f"   - {name}")

    print("\n" + "=" * 60)
    print("ГОТОВО! Реальные границы готовы к загрузке")
    print("=" * 60)

if __name__ == "__main__":
    process_geojson()
