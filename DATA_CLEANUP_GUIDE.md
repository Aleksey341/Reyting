# Инструкция по очистке данных

## Доступные методы очистки

### 1. Просмотр текущих данных

**Эндпоинт:** `GET /api/cleanup/data-stats`

Показывает статистику по всем данным в БД:
- Количество муниципалитетов
- Количество показателей
- Количество периодов
- Детали по каждому периоду (сколько значений)

**Пример:**
```bash
curl https://reyting-alex1976.amvera.io/api/cleanup/data-stats
```

**Или через Swagger:**
https://reyting-alex1976.amvera.io/docs → `GET /api/cleanup/data-stats`

---

### 2. Удалить данные конкретного периода

**Эндпоинт:** `DELETE /api/cleanup/clear-period-data?period_id={ID}&confirm=true`

Удаляет все данные для конкретного периода:
- Значения показателей (fact_indicator)
- Рассчитанные баллы (fact_summary)
- Сам период (dim_period)

**Параметры:**
- `period_id` - ID периода (посмотреть в data-stats)
- `confirm=true` - обязательное подтверждение

**Пример:**
```bash
# Удалить данные за период 2024-02 (period_id=2)
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-period-data?period_id=2&confirm=true"
```

**Через Swagger:**
1. Откройте https://reyting-alex1976.amvera.io/docs
2. `DELETE /api/cleanup/clear-period-data`
3. Укажите `period_id` и поставьте `confirm=true`
4. Execute

---

### 3. Очистить только факты (данные), оставить структуру

**Эндпоинт:** `DELETE /api/cleanup/clear-fact-data?confirm=true`

Удаляет только данные, оставляет справочники:

**Удаляется:**
- ❌ Значения показателей (fact_indicator)
- ❌ Рассчитанные баллы (fact_summary)

**Сохраняется:**
- ✅ Муниципалитеты с границами (dim_mo)
- ✅ Периоды (dim_period)
- ✅ Справочник показателей (dim_indicator)
- ✅ Методологии (dim_methodology)

**Пример:**
```bash
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-fact-data?confirm=true"
```

**Когда использовать:**
Когда нужно перезагрузить данные заново, но оставить структуру периодов и показателей.

---

### 4. ⚠️ Полная очистка всех данных

**Эндпоинт:** `DELETE /api/cleanup/clear-all-data?confirm=true`

**⚠️ ОПАСНО!** Удаляет ВСЕ данные:

**Удаляется:**
- ❌ Значения показателей (fact_indicator)
- ❌ Рассчитанные баллы (fact_summary)
- ❌ Периоды (dim_period)
- ❌ Показатели (dim_indicator)
- ❌ Методологии (dim_methodology)

**Сохраняется:**
- ✅ Муниципалитеты с границами (dim_mo)
- ✅ Структура БД (таблицы)

**Пример:**
```bash
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-all-data?confirm=true"
```

**Когда использовать:**
Когда нужно начать полностью с нуля, но оставить муниципалитеты и границы.

---

## Пошаговая инструкция

### Сценарий 1: Удалить данные одного месяца

```bash
# 1. Посмотреть список периодов
curl https://reyting-alex1976.amvera.io/api/cleanup/data-stats

# Вывод покажет:
# "period_details": [
#   {"period_id": 1, "date_from": "2024-01-01", ...},
#   {"period_id": 2, "date_from": "2024-02-01", ...}
# ]

# 2. Удалить нужный период (например, period_id=2)
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-period-data?period_id=2&confirm=true"
```

### Сценарий 2: Полностью перезагрузить данные

```bash
# 1. Очистить все данные (оставив муниципалитеты)
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-all-data?confirm=true"

# 2. Загрузить CSV заново
# Откройте https://reyting-alex1976.amvera.io/import
# Загрузите файлы для нужных периодов

# 3. Проверить что данные появились
curl https://reyting-alex1976.amvera.io/api/cleanup/data-stats
```

### Сценарий 3: Оставить справочники, удалить только данные

```bash
# Удалить только факты (данные)
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-fact-data?confirm=true"

# Периоды и показатели остались, можно загружать новые данные
```

---

## Защита от случайного удаления

Все эндпоинты требуют параметр `confirm=true`:

**Без confirm - ошибка:**
```bash
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-all-data"
# Error: "Must set confirm=True to delete all data"
```

**С confirm - работает:**
```bash
curl -X DELETE "https://reyting-alex1976.amvera.io/api/cleanup/clear-all-data?confirm=true"
# Success!
```

---

## Через Swagger UI (самый простой способ)

1. Откройте https://reyting-alex1976.amvera.io/docs
2. Найдите секцию **data-cleanup**
3. Выберите нужный эндпоинт:
   - `GET /data-stats` - посмотреть статистику
   - `DELETE /clear-period-data` - удалить период
   - `DELETE /clear-fact-data` - удалить только данные
   - `DELETE /clear-all-data` - удалить всё
4. Нажмите "Try it out"
5. Установите `confirm = true`
6. Execute

---

## Что происходит после очистки

### После удаления данных:

1. **Карта будет пустой** - нет данных для отображения
2. **Рейтинг будет пустой** - нет баллов
3. **Аналитика будет пустой** - нет графиков

### Чтобы восстановить:

1. Загрузите CSV через https://reyting-alex1976.amvera.io/import
2. Баллы пересчитаются автоматически
3. Карта и рейтинг обновятся

---

## Логирование

Все операции очистки логируются в backend:

```
[WARNING] Starting full data deletion. Current counts:
[WARNING]   - fact_indicator: 1480
[WARNING]   - fact_summary: 40
[INFO] Period 2 data deleted successfully
```

Проверьте логи Amvera после операции очистки.

---

## FAQ

**Q: Удалятся ли границы муниципалитетов?**
A: Нет! Границы (dim_mo.geojson) всегда сохраняются.

**Q: Можно ли отменить удаление?**
A: Нет. Создайте бэкап БД перед очисткой (через Amvera панель).

**Q: Что делать если случайно удалил?**
A: Восстановить из бэкапа или загрузить CSV заново.

**Q: Какой метод использовать для тестирования?**
A: `clear-fact-data` - оставляет структуру, удаляет только данные.

**Q: Нужно ли пересчитывать баллы после очистки?**
A: Нет! При загрузке CSV баллы пересчитываются автоматически.

---

## Безопасность

✅ Требуется параметр `confirm=true`
✅ Все операции логируются
✅ Муниципалитеты и границы защищены
✅ Структура БД сохраняется

⚠️ Нет подтверждения через UI - будьте осторожны!
⚠️ Операция необратима - сделайте бэкап БД
