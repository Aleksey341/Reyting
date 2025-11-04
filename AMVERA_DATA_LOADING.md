# 🚀 Загрузка Данных на Amvera Сервер

Поскольку БД на Amvera недоступна с внешних IP адресов, нужно запустить скрипт загрузки прямо на сервере Amvera.

---

## ⚠️ ПРОБЛЕМА

```
ERROR: could not translate host name "amvera-alex1976-cnpq-reyting-mo-rw" to address
```

**Причина**: БД на Amvera доступна только изнутри сети Amvera (из контейнеров).

**Решение**: Запустить скрипт загрузки в контейнере Backend на Amvera.

---

## ✅ РЕШЕНИЕ: Запуск в Backend Контейнере

### Вариант A: Через Backend Сервис (Рекомендуется)

**Шаг 1: Скопируйте файлы в контейнер**

```bash
# Откройте консоль Amvera → Backend контейнер → Terminal/Console
# Или используйте SSH доступ к контейнеру

# Скопируйте extracted_data.json в контейнер
docker cp extracted_data.json amvera_backend:/app/
docker cp etl/load_to_db.py amvera_backend:/app/
```

**Шаг 2: Запустите скрипт в контейнере**

```bash
# В терминале контейнера:
cd /app
python load_to_db.py
```

**Ожидаемый результат:**
```
🚀 ЗАГРУЗКА ДАННЫХ В POSTGRESQL НА AMVERA
✓ Успешно подключились к БД
📖 Загружаю данные из: extracted_data.json
✓ Загружено 13814 записей из JSON

======================================================================
📊 ЗАГРУЗКА ДАННЫХ В БД
======================================================================
  Обработано 1000/13814 записей...
  Обработано 2000/13814 записей...
  ...
✅ ЗАГРУЗКА ЗАВЕРШЕНА
   Загружено записей: 12500+
   Пропущено: 100
   Ошибок: 0
```

---

### Вариант B: Через pgAdmin в Консоли Amvera

Если нет прямого доступа к контейнеру:

**Шаг 1: Откройте pgAdmin**
```
https://console.amvera.ru
→ Database (PostgreSQL) → reytingdb
→ pgAdmin (или Query Editor)
```

**Шаг 2: Импортируйте данные через SQL**

```sql
-- Если у вас есть CSV файл загруженный на сервер
\COPY fact_indicator (mo_id, period_id, ind_id, value_raw, value_norm, score)
FROM '/path/to/data.csv'
WITH (FORMAT csv, HEADER);
```

Или вставьте данные напрямую через JSON (требует больше времени).

---

### Вариант C: Через Python в Backend

**Самый простой вариант:**

**Шаг 1: Создайте файл в Backend контейнере**

Создайте `/app/load_data.py`:

```python
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# БД доступна изнутри контейнера
DATABASE_URL = "postgresql://reyting_user:Qwerty12345@postgres:5432/reytingdb"
# или используйте переменную окружения
DATABASE_URL = os.getenv('DATABASE_URL', DATABASE_URL)

engine = create_engine(DATABASE_URL)
session = Session(engine)

# Читаем extracted_data.json
with open('extracted_data.json', 'r') as f:
    data = json.load(f)

# Загружаем в БД
loaded = 0
for record in data:
    try:
        mo_id = get_mo_id(session, record['mo_name'])
        period_id = get_period_id(session)
        ind_id = get_indicator_id(session, record['category'])

        if all([mo_id, period_id, ind_id]):
            value_raw = float(record['value_raw'])
            value_norm = min(100, max(0, value_raw * 100 if value_raw <= 1 else value_raw))
            score = 10 if value_norm >= 75 else (5 if value_norm >= 50 else 0)

            session.execute(
                text("""
                    INSERT INTO fact_indicator
                    (mo_id, period_id, ind_id, value_raw, value_norm, score)
                    VALUES (:mo_id, :period_id, :ind_id, :value_raw, :value_norm, :score)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "mo_id": mo_id,
                    "period_id": period_id,
                    "ind_id": ind_id,
                    "value_raw": value_raw,
                    "value_norm": value_norm,
                    "score": score
                }
            )
            loaded += 1

            if loaded % 500 == 0:
                session.commit()
                print(f"Загружено {loaded} записей...")
    except Exception as e:
        print(f"Ошибка: {e}")

session.commit()
print(f"✅ Загружено {loaded} записей")
```

**Шаг 2: Запустите в контейнере**

```bash
cd /app
python load_data.py
```

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПУТЬ

### Для Быстрой Загрузки:

1. **Скопируйте файлы на Amvera сервер** (через консоль или SFTP):
   ```bash
   scp extracted_data.json user@amvera:/tmp/
   scp etl/load_to_db.py user@amvera:/tmp/
   ```

2. **SSH в контейнер Backend**:
   ```bash
   ssh -i key.pem backend@amvera-...-mo.amvera.io
   ```

3. **Запустите скрипт**:
   ```bash
   python /tmp/load_to_db.py
   ```

4. **Проверьте результаты**:
   ```bash
   psql -h localhost -U reyting_user -d reytingdb -c "SELECT COUNT(*) FROM fact_indicator;"
   ```

---

## 📊 АЛЬТЕРНАТИВА: SQL INSERT Напрямую

Если JSON слишком большой, можно импортировать CSV прямо:

**Шаг 1: Создайте CSV из JSON**

```python
import json
import csv

with open('extracted_data.json', 'r') as f:
    data = json.load(f)

with open('data_for_import.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['mo_id', 'period_id', 'ind_id', 'value_raw', 'value_norm', 'score'])
    writer.writeheader()

    for record in data:
        # Преобразуем в формат для fact_indicator
        # (нужно знать mo_id, ind_id и т.д.)
        writer.writerow({...})
```

**Шаг 2: В pgAdmin выполните**

```sql
\COPY fact_indicator FROM '/tmp/data_for_import.csv' WITH CSV HEADER;
```

---

## ✅ ПРОВЕРКА ПОСЛЕ ЗАГРУЗКИ

```sql
-- Проверить количество записей
SELECT COUNT(*) as total FROM fact_indicator;

-- Проверить по МО
SELECT mo.mo_name, COUNT(*) as count
FROM fact_indicator fi
JOIN dim_mo mo ON fi.mo_id = mo.mo_id
GROUP BY mo.mo_id, mo.mo_name
ORDER BY count DESC;

-- Проверить по индикаторам
SELECT ind.name, COUNT(*) as count
FROM fact_indicator fi
JOIN dim_indicator ind ON fi.ind_id = ind.ind_id
GROUP BY fi.ind_id, ind.name
ORDER BY count DESC;
```

---

## 🔗 ПРОВЕРИТЬ FRONTEND

После загрузки откройте:
```
https://reyting.amvera.ru
```

Должны видеть:
- ✓ Таблицу рейтинга со всеми МО
- ✓ Карту с раскраской
- ✓ Аналитику по показателям

---

## 🆘 ЕСЛИ НУЖНА ПОМОЩЬ

Напишите что произошло:
1. Какую ошибку получили?
2. На каком шаге?
3. Какой вариант пробовали?

Я помогу адаптировать скрипт под вашу ситуацию.

---

**Версия**: 1.0.0
**Дата**: 04.11.2025
**Статус**: ГОТОВО К ИСПОЛЬЗОВАНИЮ
