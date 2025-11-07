# Инструкция по загрузке реальных границ муниципалитетов

## Обзор

Проект поддерживает отображение реальных границ муниципалитетов Липецкой области на интерактивной карте. Границы хранятся в PostgreSQL в формате GeoJSON и отображаются через React + Leaflet.

## Файлы с границами

В проекте доступны следующие файлы:

- **lipetsk_boundaries_real_full.geojson** - Реальные границы из OpenStreetMap (20 муниципалитетов)
- fetch_lipetsk_boundaries.py - Скрипт для получения границ из Overpass API

## Способ 1: Загрузка через API (рекомендуется)

### Шаг 1: Запустите backend локально

```bash
cd backend
uvicorn main:app --reload
```

Backend будет доступен на http://localhost:8000

### Шаг 2: Загрузите файл с границами

Используйте curl или Postman:

```bash
curl -X POST \
  -F "file=@lipetsk_boundaries_real_full.geojson" \
  http://localhost:8000/api/import/upload-real-boundaries
```

Или через Swagger UI:
1. Откройте http://localhost:8000/docs
2. Найдите эндпоинт `POST /api/import/upload-real-boundaries`
3. Нажмите "Try it out"
4. Загрузите файл `lipetsk_boundaries_real_full.geojson`
5. Нажмите "Execute"

### Шаг 3: Проверьте результат

API вернет информацию об обновлении:

```json
{
  "status": "success",
  "message": "Uploaded real boundaries for 20 municipalities",
  "updated": 20,
  "not_found": [],
  "errors": [],
  "note": "Real boundaries from GeoJSON FeatureCollection"
}
```

## Способ 2: Загрузка через продакшн (Amvera)

После деплоя на Amvera:

```bash
curl -X POST \
  -F "file=@lipetsk_boundaries_real_full.geojson" \
  https://your-app.amvera.io/api/import/upload-real-boundaries
```

## Формат файла

Эндпоинт принимает стандартный GeoJSON FeatureCollection:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Липецк"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon, lat], ...]]
      }
    }
  ]
}
```

### Важные требования:

1. **properties.name** должен совпадать с названием МО в базе данных
2. Поиск по названию **регистронезависимый** (case-insensitive)
3. Поддерживаются типы геометрии: `Polygon` и `MultiPolygon`

## Получение новых границ

Если нужно обновить границы или получить для других регионов:

```bash
# Отредактируйте fetch_lipetsk_boundaries.py (измените ISO3166-2 код)
python fetch_lipetsk_boundaries.py
```

Скрипт создаст файл `lipetsk_boundaries_real_full.geojson` с актуальными границами из OpenStreetMap.

## Соответствие названий

Муниципалитеты в БД:

1. Липецк
2. Елец
3. Воловский
4. Грязянский → **Грязинский район**
5. Данковский
6. Добринский
7. Добровский
8. Долгоруковский
9. Елецкий
10. Задонский
11. Измалковский
12. Краснинский
13. Лебедянский
14. Лев-Толстовский
15. Липецкий
16. Становлянский
17. Тербунский
18. Усманский
19. Хлевенский
20. Чаплыгинский

**Примечание:** Если название в GeoJSON не совпадает с БД, оно будет в списке `not_found`. Проверьте правильность написания.

## Проверка на карте

После загрузки границ:

1. Откройте дашборд
2. Перейдите на вкладку "Карта"
3. Границы должны отображаться с реальной геометрией
4. При наведении - подсветка
5. При клике - всплывающее окно с информацией
6. Легенда показывает зоны по цветам

## Troubleshooting

### Проблема: "Municipality not found in DB"

**Решение:** Проверьте соответствие названий в GeoJSON и БД. Используйте регистронезависимый поиск.

### Проблема: "Feature missing geometry"

**Решение:** Убедитесь, что в GeoJSON есть поле `geometry` для каждого Feature.

### Проблема: Карта показывает прямоугольники вместо реальных границ

**Решение:**
1. Проверьте, что границы загружены через API
2. Проверьте SQL: `SELECT mo_name, geojson FROM dim_mo LIMIT 1;`
3. Убедитесь, что `geojson` содержит реальную геометрию

## Технические детали

### Backend

- **Эндпоинт:** `/api/import/upload-real-boundaries` (POST)
- **Файл:** `backend/routes/data_import_routes.py:487-609`
- **База:** PostgreSQL, колонка `dim_mo.geojson` (JSONB)

### Frontend

- **Компонент:** `frontend/src/components/InteractiveMap.jsx`
- **Библиотека:** react-leaflet v4
- **Формат:** GeoJSON FeatureCollection
- **Стили:** По зонам (green/yellow/red)

### Map API

- **Эндпоинт:** `/api/map/data` (GET)
- **Файл:** `backend/routes/map_routes.py`
- **Возвращает:** GeoJSON с метриками по периодам
