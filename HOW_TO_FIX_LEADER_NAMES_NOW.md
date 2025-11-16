# 🔧 КАК БЫСТРО ЗАПОЛНИТЬ ФИО ГЛАВ МО

## ⚡ СРОЧНО: Нужно выполнить эту команду на production БД!

---

## **ВАРИАНТ 1: Через консоль Amvera (САМЫЙ ПРОСТОЙ)**

1. Откройте https://console.amvera.ru
2. Выберите приложение **Reyting**
3. Перейдите в **Database** → **PostgreSQL** → **reytingdb**
4. Нажмите **SQL Query** или **Query Editor**
5. **Скопируйте и вставьте весь текст ниже:**

```sql
BEGIN;

ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);

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

SELECT COUNT(*) as leaders_updated FROM dim_mo WHERE leader_name IS NOT NULL;
SELECT mo_name, leader_name FROM dim_mo WHERE leader_name IS NOT NULL ORDER BY mo_name;

COMMIT;
```

6. Нажмите **Execute** или **Run**
7. ✅ Готово! ФИО заполнены

---

## **ВАРИАНТ 2: Через SSH на Amvera**

```bash
# Подключиться к контейнеру
amvera ssh

# Выполнить SQL команду
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -f /app/backend/migrations/APPLY_LEADER_NAMES_NOW.sql
```

---

## **ВАРИАНТ 3: С локальной машины**

```bash
# Установить пароль
export PGPASSWORD="ваш_пароль_из_amvera_console"

# Выполнить команду
psql -U reyting_user -d reytingdb -h amvera-alex1976-cnpq-reyting-mo-rw -p 5432 \
  -f backend/migrations/APPLY_LEADER_NAMES_NOW.sql
```

---

## ✅ Проверка

После выполнения выполните:

```sql
SELECT COUNT(*) FROM dim_mo WHERE leader_name IS NOT NULL;
```

Должно быть: **20** (20 муниципальных образований с ФИО)

---

## 🔄 После этого

1. ✅ Откройте браузер и перейдите на https://reyting-alex1976.amvera.io/
2. ✅ Нажмите на вкладку "Рейтинг"
3. ✅ ФИО глав должны быть видны во втором столбце!

---

## 📞 Если ФИО все еще не видны

1. Очистите кэш браузера (Ctrl+Shift+Delete)
2. Откройте https://reyting-alex1976.amvera.io/ заново
3. Проверьте в F12 → Network → GET /api/rating что `leader_name` есть в ответе

---

**Это займет 30 секунд максимум!** ⚡
