#!/usr/bin/env python3
"""
Исправление названий муниципалитетов в GeoJSON для соответствия БД
"""
import json
import sys

# Маппинг: OSM название → Название в БД (точные названия из backend/routes/data_import_routes.py)
NAME_MAPPING = {
    # Городские округа
    "городской округ Липецк": "Липецк",
    "городской округ Елец": "Елец",

    # Районы (в БД без суффиксов "район", "муниципальный округ")
    "Грязинский район": "Грязянский",  # ВАЖНО: в БД "Грязянский" с буквой "я"!
    "Воловский муниципальный округ": "Воловский",
    "Тербунский район": "Тербунский",
    "Добринский район": "Добринский",
    "Липецкий муниципальный округ": "Липецкий",
    "Усманский район": "Усманский",
    "Добровский муниципальный округ": "Добровский",
    "Чаплыгинский район": "Чаплыгинский",
    "Лев-Толстовский район": "Лев-Толстовский",
    "Данковский район": "Данковский",
    "Лебедянский район": "Лебедянский",
    "Краснинский район": "Краснинский",
    "Задонский район": "Задонский",
    "Хлевенский район": "Хлевенский",
    "Елецкий район": "Елецкий",
    "Долгоруковский район": "Долгоруковский",
    "Измалковский муниципальный округ": "Измалковский",
    "Становлянский муниципальный округ": "Становлянский",
}


def fix_names(input_file, output_file):
    """Fix municipality names in GeoJSON"""
    print(f"Reading {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('type') != 'FeatureCollection':
        print("Error: Not a FeatureCollection")
        return False

    features = data.get('features', [])
    print(f"Found {len(features)} features")
    print()

    fixed_count = 0
    not_found = []

    for i, feature in enumerate(features):
        props = feature.get('properties', {})
        original_name = props.get('name', '')

        if original_name in NAME_MAPPING:
            new_name = NAME_MAPPING[original_name]
            props['name'] = new_name
            props['original_name'] = original_name  # Сохраняем оригинал
            fixed_count += 1
            print(f"[OK] {original_name} -> {new_name}")
        else:
            not_found.append(original_name)
            print(f"[SKIP] {original_name} (not in mapping)")

    print()
    print(f"Fixed: {fixed_count}")
    print(f"Not mapped: {len(not_found)}")

    if not_found:
        print()
        print("Not mapped names:")
        for name in not_found:
            print(f"  - {name}")

    # Save
    print()
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done! Fixed {fixed_count} names")
    return True


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python fix_boundary_names.py input.geojson output.geojson")
        print()
        print("Example:")
        print("  python fix_boundary_names.py lipetsk_municipalities_clean.geojson lipetsk_fixed.geojson")
        sys.exit(1)

    success = fix_names(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
