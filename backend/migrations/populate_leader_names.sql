-- Migration: Populate real leader names for all municipalities
-- Date: 2025-11-16
-- Purpose: Fill dim_mo.leader_name with actual municipal leaders

BEGIN;

-- 1. First, ensure leader_name column exists (in case migration wasn't applied yet)
-- This is safe because of IF NOT EXISTS
ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);

-- 2. Update with real leader names from Липецкой области
-- Data source: Official municipal registry

UPDATE dim_mo SET leader_name = 'Ченцов Р.И.'
WHERE mo_name LIKE '%Липецк%' AND mo_name NOT LIKE '%Липецкий%';

UPDATE dim_mo SET leader_name = 'Жабин В.П.'
WHERE mo_name LIKE '%Елец%' AND mo_name NOT LIKE '%Елецкий%';

UPDATE dim_mo SET leader_name = 'Щеглов С.С.'
WHERE mo_name LIKE '%Воловский%';

UPDATE dim_mo SET leader_name = 'Рощупкин В.Т.'
WHERE mo_name LIKE '%Грязянский%';

UPDATE dim_mo SET leader_name = 'Фалеев В.И.'
WHERE mo_name LIKE '%Данковский%';

UPDATE dim_mo SET leader_name = 'Пасынков А.Н.'
WHERE mo_name LIKE '%Добринский%';

UPDATE dim_mo SET leader_name = 'Попов А.А.'
WHERE mo_name LIKE '%Добровский%';

UPDATE dim_mo SET leader_name = 'Тимохин А.Н.'
WHERE mo_name LIKE '%Долгоруковский%';

UPDATE dim_mo SET leader_name = 'Семенихин О.Н.'
WHERE mo_name LIKE '%Елецкий%';

UPDATE dim_mo SET leader_name = 'Щедров А.И.'
WHERE mo_name LIKE '%Задонский%';

UPDATE dim_mo SET leader_name = 'Иванников В.Ю.'
WHERE mo_name LIKE '%Измалковский%';

UPDATE dim_mo SET leader_name = 'Поляков С.О.'
WHERE mo_name LIKE '%Краснинский%';

UPDATE dim_mo SET leader_name = 'Телков А.М.'
WHERE mo_name LIKE '%Лебедянский%';

UPDATE dim_mo SET leader_name = 'Шабанов К.Ю.'
WHERE mo_name LIKE '%Лев-Толстовский%';

UPDATE dim_mo SET leader_name = 'Тодуа Д.В.'
WHERE mo_name LIKE '%Липецкий%';

UPDATE dim_mo SET leader_name = 'Семянников Д.Ю.'
WHERE mo_name LIKE '%Становлянский%';

UPDATE dim_mo SET leader_name = 'Черников Н.Е.'
WHERE mo_name LIKE '%Тербунский%';

UPDATE dim_mo SET leader_name = 'Мазо В.М.'
WHERE mo_name LIKE '%Усманский%';

UPDATE dim_mo SET leader_name = 'Плотников А.И.'
WHERE mo_name LIKE '%Хлевенский%';

UPDATE dim_mo SET leader_name = 'Сазонов Ю.А.'
WHERE mo_name LIKE '%Чаплыгинский%';

-- 3. Verification: Show all municipalities with leader names
SELECT COUNT(*) as updated_records FROM dim_mo WHERE leader_name IS NOT NULL;

-- 4. Show the updated data
SELECT mo_id, mo_name, leader_name FROM dim_mo WHERE leader_name IS NOT NULL ORDER BY mo_name;

COMMIT;
