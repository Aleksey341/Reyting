"""
Создание более реалистичных границ для муниципалитетов
на основе их центральных координат.
Использует круговые/эллиптические полигоны вместо прямоугольников.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import math

# Координаты центров муниципалитетов Липецкой области
MUNICIPALITIES = {
    "Липецк": {"lat": 52.6031, "lon": 39.5708, "size": 0.12},
    "Елец": {"lat": 52.6236, "lon": 38.5019, "size": 0.12},
    "Воловский": {"lat": 51.1528, "lon": 38.4500, "size": 0.20},
    "Грязянский": {"lat": 52.5000, "lon": 39.9500, "size": 0.18},
    "Данковский": {"lat": 53.2500, "lon": 39.1500, "size": 0.22},
    "Добринский": {"lat": 52.2000, "lon": 40.4000, "size": 0.20},
    "Добровский": {"lat": 52.3500, "lon": 39.2000, "size": 0.18},
    "Долгоруковский": {"lat": 52.3500, "lon": 38.3000, "size": 0.19},
    "Елецкий": {"lat": 52.6236, "lon": 38.5019, "size": 0.25},
    "Задонский": {"lat": 52.4000, "lon": 38.9000, "size": 0.20},
    "Измалковский": {"lat": 52.5000, "lon": 38.8000, "size": 0.18},
    "Краснинский": {"lat": 53.0000, "lon": 39.5000, "size": 0.21},
    "Лебедянский": {"lat": 53.0200, "lon": 39.1300, "size": 0.20},
    "Лев-Толстовский": {"lat": 52.1000, "lon": 39.5000, "size": 0.17},
    "Липецкий": {"lat": 52.6031, "lon": 39.5708, "size": 0.28},
    "Становлянский": {"lat": 53.0000, "lon": 38.5000, "size": 0.19},
    "Тербунский": {"lat": 52.1500, "lon": 38.2500, "size": 0.20},
    "Усманский": {"lat": 52.0500, "lon": 39.7400, "size": 0.22},
    "Хлевенский": {"lat": 52.4500, "lon": 38.1000, "size": 0.19},
    "Чаплыгинский": {"lat": 53.2500, "lon": 39.9500, "size": 0.21},
}

def create_circular_polygon(lat, lon, size, points=36):
    """
    Создает круговой полигон вокруг точки.

    Args:
        lat: широта центра
        lon: долгота центра
        size: размер (радиус) в градусах
        points: количество точек полигона
    """
    coordinates = []

    for i in range(points):
        angle = (i * 360 / points) * (math.pi / 180)

        # Добавляем небольшую случайность для более естественной формы
        # Используем вариацию радиуса на основе угла
        radius_variation = 1.0 + 0.2 * math.sin(3 * angle)  # Волнообразная граница
        current_size = size * radius_variation

        point_lat = lat + current_size * math.sin(angle)
        point_lon = lon + current_size * math.cos(angle) / math.cos(lat * math.pi / 180)

        coordinates.append([point_lon, point_lat])

    # Замыкаем полигон
    coordinates.append(coordinates[0])

    return {
        "type": "Polygon",
        "coordinates": [coordinates]
    }

def create_elliptical_polygon(lat, lon, size, points=36, eccentricity=1.5):
    """
    Создает эллиптический полигон с неровными краями.

    Args:
        lat: широта центра
        lon: долгота центра
        size: базовый размер
        points: количество точек
        eccentricity: соотношение осей эллипса
    """
    coordinates = []

    for i in range(points):
        angle = (i * 360 / points) * (math.pi / 180)

        # Эллиптическая форма с вариацией
        a = size * eccentricity  # Большая полуось
        b = size  # Малая полуось

        # Добавляем волнистость границ
        wave = 1.0 + 0.15 * math.sin(5 * angle) + 0.1 * math.cos(7 * angle)

        r = (a * b) / math.sqrt((b * math.cos(angle))**2 + (a * math.sin(angle))**2)
        r *= wave

        point_lat = lat + r * math.sin(angle)
        point_lon = lon + r * math.cos(angle) / math.cos(lat * math.pi / 180)

        coordinates.append([point_lon, point_lat])

    # Замыкаем полигон
    coordinates.append(coordinates[0])

    return {
        "type": "Polygon",
        "coordinates": [coordinates]
    }

def create_boundaries():
    """Создать границы для всех муниципалитетов"""
    print("=" * 60)
    print("Создание реалистичных границ муниципалитетов")
    print("=" * 60)

    boundaries = {}

    for name, data in MUNICIPALITIES.items():
        lat = data['lat']
        lon = data['lon']
        size = data['size']

        # Используем эллиптический полигон для более естественного вида
        geojson = create_elliptical_polygon(lat, lon, size, points=48)

        boundaries[name] = geojson
        point_count = len(geojson['coordinates'][0])

        print(f"  ✓ {name:20s} - {point_count} точек (размер: {size:.2f}°)")

    return boundaries

def save_to_json(boundaries, filename="lipetsk_boundaries_realistic.json"):
    """Сохранить в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Сохранено в {filename}")

def main():
    boundaries = create_boundaries()

    print(f"\n📊 Создано границ: {len(boundaries)} муниципалитетов")

    save_to_json(boundaries)

    print("\n" + "=" * 60)
    print("ГОТОВО! Границы созданы на основе координат центров")
    print("=" * 60)
    print("Границы имеют эллиптическую форму с волнистыми краями")
    print("для более естественного вида")
    print("\nСледующий шаг: загрузить в базу данных")

if __name__ == "__main__":
    main()
