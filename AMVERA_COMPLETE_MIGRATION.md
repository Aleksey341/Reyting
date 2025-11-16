# Полная миграция на Amvera: Добавление колонки и заполнение ФИО глав

## 📋 Этапы миграции

Миграция состоит из двух этапов:

### **Этап 1: Добавить колонку `leader_name`** (обязательно)
### **Этап 2: Заполнить ФИО глав МО** (обязательно)

---

## 🚀 Способ 1: Через SSH на Amvera (Рекомендуется)

### Шаг 1: Подключиться к контейнеру
```bash
amvera ssh
```

### Шаг 2: Подключиться к БД
```bash
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432
```

### Шаг 3: Добавить колонку
```sql
ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_dim_mo_leader_name ON dim_mo(leader_name);
```

### Шаг 4: Заполнить ФИО глав
```sql
BEGIN;

UPDATE dim_mo SET leader_name = 'Ченцов Р.И.' WHERE mo_name LIKE '%Липецк%' AND mo_name NOT LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Жабин В.П.' WHERE mo_name LIKE '%Елец%' AND mo_name NOT LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щеглов С.С.' WHERE mo_name LIKE '%Воловский%';
UPDATE dim_mo SET leader_name = 'Рощупкин В.Т.' WHERE mo_name LIKE '%Грязянский%';
UPDATE dim_mo SET leader_name = 'Фалеев В.И.' WHERE mo_name LIKE '%Данковский%';
UPDATE dim_mo SET leader_name = 'Пасынков А.Н.' WHERE mo_name LIKE '%Добринский%';
UPDATE dim_mo SET leader_name = 'Попов А.А.' WHERE mo_name LIKE '%Добровский%';
UPDATE dim_mo SET leader_name = 'Тимохин А.Н.' WHERE mo_name LIKE '%Долгоруковский%';
UPDATE dim_mo SET leader_name = 'Семенихин О.Н.' WHERE mo_name LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щедров А.И.' WHERE mo_name LIKE '%Задонский%';
UPDATE dim_mo SET leader_name = 'Иванников В.Ю.' WHERE mo_name LIKE '%Измалковский%';
UPDATE dim_mo SET leader_name = 'Поляков С.О.' WHERE mo_name LIKE '%Краснинский%';
UPDATE dim_mo SET leader_name = 'Телков А.М.' WHERE mo_name LIKE '%Лебедянский%';
UPDATE dim_mo SET leader_name = 'Шабанов К.Ю.' WHERE mo_name LIKE '%Лев-Толстовский%';
UPDATE dim_mo SET leader_name = 'Тодуа Д.В.' WHERE mo_name LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Семянников Д.Ю.' WHERE mo_name LIKE '%Становлянский%';
UPDATE dim_mo SET leader_name = 'Черников Н.Е.' WHERE mo_name LIKE '%Тербунский%';
UPDATE dim_mo SET leader_name = 'Мазо В.М.' WHERE mo_name LIKE '%Усманский%';
UPDATE dim_mo SET leader_name = 'Плотников А.И.' WHERE mo_name LIKE '%Хлевенский%';
UPDATE dim_mo SET leader_name = 'Сазонов Ю.А.' WHERE mo_name LIKE '%Чаплыгинский%';

COMMIT;
```

### Шаг 5: Проверить результат
```sql
-- Проверить, что колонка добавлена
\d dim_mo

-- Проверить, что данные заполнены
SELECT mo_id, mo_name, leader_name FROM dim_mo WHERE leader_name IS NOT NULL ORDER BY mo_name;

-- Выход из psql
\q
```

---

## 🚀 Способ 2: Выполнить SQL файл из контейнера

### Шаг 1: Подключиться к контейнеру
```bash
amvera ssh
```

### Шаг 2: Выполнить миграцию колонки
```bash
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -f /app/backend/migrations/add_leader_name_to_mo.sql
```

### Шаг 3: Выполнить заполнение ФИО
```bash
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -f /app/backend/migrations/populate_leader_names.sql
```

---

## 🚀 Способ 3: Через Amvera веб-консоль

### Шаг 1: Откройте консоль
1. Откройте https://console.amvera.ru
2. Авторизуйтесь
3. Выберите приложение Reyting
4. Перейдите в Database → PostgreSQL → reytingdb
5. Откройте SQL Query editor

### Шаг 2: Выполните все команды подряд
Скопируйте и вставьте весь блок (или выполняйте по частям):

```sql
-- Добавить колонку
ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_dim_mo_leader_name ON dim_mo(leader_name);

-- Заполнить ФИО глав
UPDATE dim_mo SET leader_name = 'Ченцов Р.И.' WHERE mo_name LIKE '%Липецк%' AND mo_name NOT LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Жабин В.П.' WHERE mo_name LIKE '%Елец%' AND mo_name NOT LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щеглов С.С.' WHERE mo_name LIKE '%Воловский%';
UPDATE dim_mo SET leader_name = 'Рощупкин В.Т.' WHERE mo_name LIKE '%Грязянский%';
UPDATE dim_mo SET leader_name = 'Фалеев В.И.' WHERE mo_name LIKE '%Данковский%';
UPDATE dim_mo SET leader_name = 'Пасынков А.Н.' WHERE mo_name LIKE '%Добринский%';
UPDATE dim_mo SET leader_name = 'Попов А.А.' WHERE mo_name LIKE '%Добровский%';
UPDATE dim_mo SET leader_name = 'Тимохин А.Н.' WHERE mo_name LIKE '%Долгоруковский%';
UPDATE dim_mo SET leader_name = 'Семенихин О.Н.' WHERE mo_name LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щедров А.И.' WHERE mo_name LIKE '%Задонский%';
UPDATE dim_mo SET leader_name = 'Иванников В.Ю.' WHERE mo_name LIKE '%Измалковский%';
UPDATE dim_mo SET leader_name = 'Поляков С.О.' WHERE mo_name LIKE '%Краснинский%';
UPDATE dim_mo SET leader_name = 'Телков А.М.' WHERE mo_name LIKE '%Лебедянский%';
UPDATE dim_mo SET leader_name = 'Шабанов К.Ю.' WHERE mo_name LIKE '%Лев-Толстовский%';
UPDATE dim_mo SET leader_name = 'Тодуа Д.В.' WHERE mo_name LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Семянников Д.Ю.' WHERE mo_name LIKE '%Становлянский%';
UPDATE dim_mo SET leader_name = 'Черников Н.Е.' WHERE mo_name LIKE '%Тербунский%';
UPDATE dim_mo SET leader_name = 'Мазо В.М.' WHERE mo_name LIKE '%Усманский%';
UPDATE dim_mo SET leader_name = 'Плотников А.И.' WHERE mo_name LIKE '%Хлевенский%';
UPDATE dim_mo SET leader_name = 'Сазонов Ю.А.' WHERE mo_name LIKE '%Чаплыгинский%';

-- Проверка
SELECT COUNT(*) as updated_records FROM dim_mo WHERE leader_name IS NOT NULL;
```

Нажмите **Execute** или **Run Query**

---

## 🚀 Способ 4: Через командную строку (Windows/macOS)

```bash
# Установить переменную с паролем
$env:PGPASSWORD = "your_password"  # Windows PowerShell
# или
export PGPASSWORD="your_password"  # macOS/Linux

# Выполнить миграцию колонки
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -c "ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);"

psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -c "CREATE INDEX IF NOT EXISTS idx_dim_mo_leader_name ON dim_mo(leader_name);"

# Выполнить заполнение ФИО
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -c "BEGIN; UPDATE dim_mo SET leader_name = 'Ченцов Р.И.' WHERE mo_name LIKE '%Липецк%' AND mo_name NOT LIKE '%Липецкий%'; UPDATE dim_mo SET leader_name = 'Жабин В.П.' WHERE mo_name LIKE '%Елец%' AND mo_name NOT LIKE '%Елецкий%'; UPDATE dim_mo SET leader_name = 'Щеглов С.С.' WHERE mo_name LIKE '%Воловский%'; UPDATE dim_mo SET leader_name = 'Рощупкин В.Т.' WHERE mo_name LIKE '%Грязянский%'; UPDATE dim_mo SET leader_name = 'Фалеев В.И.' WHERE mo_name LIKE '%Данковский%'; UPDATE dim_mo SET leader_name = 'Пасынков А.Н.' WHERE mo_name LIKE '%Добринский%'; UPDATE dim_mo SET leader_name = 'Попов А.А.' WHERE mo_name LIKE '%Добровский%'; UPDATE dim_mo SET leader_name = 'Тимохин А.Н.' WHERE mo_name LIKE '%Долгоруковский%'; UPDATE dim_mo SET leader_name = 'Семенихин О.Н.' WHERE mo_name LIKE '%Елецкий%'; UPDATE dim_mo SET leader_name = 'Щедров А.И.' WHERE mo_name LIKE '%Задонский%'; UPDATE dim_mo SET leader_name = 'Иванников В.Ю.' WHERE mo_name LIKE '%Измалковский%'; UPDATE dim_mo SET leader_name = 'Поляков С.О.' WHERE mo_name LIKE '%Краснинский%'; UPDATE dim_mo SET leader_name = 'Телков А.М.' WHERE mo_name LIKE '%Лебедянский%'; UPDATE dim_mo SET leader_name = 'Шабанов К.Ю.' WHERE mo_name LIKE '%Лев-Толстовский%'; UPDATE dim_mo SET leader_name = 'Тодуа Д.В.' WHERE mo_name LIKE '%Липецкий%'; UPDATE dim_mo SET leader_name = 'Семянников Д.Ю.' WHERE mo_name LIKE '%Становлянский%'; UPDATE dim_mo SET leader_name = 'Черников Н.Е.' WHERE mo_name LIKE '%Тербунский%'; UPDATE dim_mo SET leader_name = 'Мазо В.М.' WHERE mo_name LIKE '%Усманский%'; UPDATE dim_mo SET leader_name = 'Плотников А.И.' WHERE mo_name LIKE '%Хлевенский%'; UPDATE dim_mo SET leader_name = 'Сазонов Ю.А.' WHERE mo_name LIKE '%Чаплыгинский%'; COMMIT;"
```

---

## ✅ Проверка успеха миграции

### 1. Проверить в БД
```sql
-- Подключиться к psql и выполнить
SELECT COUNT(*) as total_with_leaders FROM dim_mo WHERE leader_name IS NOT NULL;

-- Должен вернуться: 20 (или 20 из всех муниципалитетов)
```

### 2. Проверить через API
```bash
curl "https://reyting-alex1976.amvera.io/api/rating?period=2024-01&page=1"
```

Ожидаемый результат (leader_name заполнены):
```json
{
  "status": "success",
  "data": [
    {
      "mo_id": 1,
      "mo_name": "Липецк",
      "leader_name": "Ченцов Р.И.",
      "score_total": 61,
      "zone": "green",
      ...
    }
  ]
}
```

### 3. Проверить в браузере
1. Откройте https://reyting-alex1976.amvera.io
2. Перейдите на вкладку "Рейтинг"
3. Таблица должна загруситься с ФИО глав

---

## 📊 Соответствие МО и ФИО глав

| МО | ФИО главы |
|---|---|
| Липецк | Ченцов Р.И. |
| Елец | Жабин В.П. |
| Воловский | Щеглов С.С. |
| Грязянский | Рощупкин В.Т. |
| Данковский | Фалеев В.И. |
| Добринский | Пасынков А.Н. |
| Добровский | Попов А.А. |
| Долгоруковский | Тимохин А.Н. |
| Елецкий | Семенихин О.Н. |
| Задонский | Щедров А.И. |
| Измалковский | Иванников В.Ю. |
| Краснинский | Поляков С.О. |
| Лебедянский | Телков А.М. |
| Лев-Толстовский | Шабанов К.Ю. |
| Липецкий | Тодуа Д.В. |
| Становлянский | Семянников Д.Ю. |
| Тербунский | Черников Н.Е. |
| Усманский | Мазо В.М. |
| Хлевенский | Плотников А.И. |
| Чаплыгинский | Сазонов Ю.А. |

---

## 🔧 Решение проблем

### Ошибка: "column already exists"
```
ERROR: column "leader_name" of relation "dim_mo" already exists
```
**Решение:** Миграция уже была применена! Это нормально, продолжайте с заполнением ФИО.

### Ошибка: "UPDATE не изменил строки"
```
UPDATE 0
```
**Решение:** Проверьте названия МО в БД. Может быть другое форматирование (заглавные/строчные буквы, пробелы).

Проверить с помощью:
```sql
SELECT DISTINCT mo_name FROM dim_mo ORDER BY mo_name;
```

Затем обновить условия WHERE в UPDATE запросах.

### Ошибка: "permission denied"
```
ERROR: permission denied for schema public
```
**Решение:** Пользователь `reyting_user` не имеет необходимых прав. Свяжитесь с поддержкой Amvera.

---

## 📝 После успешной миграции

1. ✅ **Перезагрузить фронтенд** (очистить кэш в браузере)
2. ✅ **Проверить вкладку "Рейтинг"** - должны видны ФИО глав
3. ✅ **Проверить API** - должны возвращаться реальные имена
4. ✅ **Протестировать сортировку и поиск** - по ФИО

---

## 🎯 Рекомендуемый порядок действий

1. ✅ Выполнить Способ 1 (SSH) или Способ 3 (веб-консоль) - выбрать удобный
2. ✅ Проверить результат в БД (SELECT COUNT)
3. ✅ Проверить API (curl)
4. ✅ Обновить браузер и проверить в UI

---

**Дата:** 16 ноября 2025
**Версия:** 2.0
**Статус:** Готово к применению на production
