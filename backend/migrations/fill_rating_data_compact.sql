-- Компактная версия скрипта заполнения БД для быстрого тестирования
-- Создает только необходимые данные для вкладки "Рейтинг"

BEGIN;

-- 1. Убедиться что есть период 2024-01
INSERT INTO dim_period (period_type, date_from, date_to, edg_flag)
SELECT 'month', '2024-01-01'::date, '2024-01-31'::date, false
WHERE NOT EXISTS (
    SELECT 1 FROM dim_period
    WHERE date_from = '2024-01-01'::date
);

-- 2. Убедиться что есть методика v1.0
INSERT INTO dim_methodology (version, valid_from, valid_to, notes)
SELECT 'v1.0', CURRENT_DATE, NULL, 'Базовая версия'
WHERE NOT EXISTS (SELECT 1 FROM dim_methodology WHERE version = 'v1.0');

-- 3. Создать простой рейтинг на основе имеющихся данных в dim_mo
-- Если fact_summary уже заполнена, это обновит существующие записи

INSERT INTO fact_summary (mo_id, period_id, version_id, score_public, score_closed, score_penalties, score_total, zone)
SELECT
    mo.mo_id,
    p.period_id,
    v.version_id,
    -- Генерируем баллы на основе порядка МО
    CASE
        WHEN mo_id = 1 THEN 55::numeric
        WHEN mo_id = 2 THEN 50::numeric
        WHEN mo_id = 3 THEN 50::numeric
        WHEN mo_id = 4 THEN 52::numeric
        WHEN mo_id = 5 THEN 48::numeric
        WHEN mo_id = 6 THEN 36::numeric
        WHEN mo_id = 7 THEN 34::numeric
        WHEN mo_id = 8 THEN 34::numeric
        WHEN mo_id = 9 THEN 34::numeric
        WHEN mo_id = 10 THEN 34::numeric
        WHEN mo_id = 11 THEN 29::numeric
        WHEN mo_id = 12 THEN 29::numeric
        WHEN mo_id = 13 THEN 26::numeric
        WHEN mo_id = 14 THEN 25::numeric
        WHEN mo_id = 15 THEN 25::numeric
        WHEN mo_id = 16 THEN 25::numeric
        WHEN mo_id = 17 THEN 25::numeric
        WHEN mo_id = 18 THEN 25::numeric
        WHEN mo_id = 19 THEN 25::numeric
        WHEN mo_id = 20 THEN 25::numeric
        ELSE ROUND(RANDOM() * 40 + 20)::numeric
    END as score_public,
    0::numeric as score_closed,
    CASE
        WHEN mo_id IN (1,2,3,4,5,6,7,8,9,10,11,12) THEN -1::numeric
        ELSE 0::numeric
    END as score_penalties,
    CASE
        WHEN mo_id = 1 THEN 61::numeric
        WHEN mo_id = 2 THEN 56::numeric
        WHEN mo_id = 3 THEN 56::numeric
        WHEN mo_id = 4 THEN 52::numeric
        WHEN mo_id = 5 THEN 48::numeric
        WHEN mo_id = 6 THEN 36::numeric
        WHEN mo_id = 7 THEN 34::numeric
        WHEN mo_id = 8 THEN 34::numeric
        WHEN mo_id = 9 THEN 34::numeric
        WHEN mo_id = 10 THEN 34::numeric
        WHEN mo_id = 11 THEN 29::numeric
        WHEN mo_id = 12 THEN 29::numeric
        WHEN mo_id = 13 THEN 26::numeric
        WHEN mo_id = 14 THEN 25::numeric
        WHEN mo_id = 15 THEN 25::numeric
        WHEN mo_id = 16 THEN 25::numeric
        WHEN mo_id = 17 THEN 25::numeric
        WHEN mo_id = 18 THEN 25::numeric
        WHEN mo_id = 19 THEN 25::numeric
        WHEN mo_id = 20 THEN 25::numeric
        ELSE ROUND(RANDOM() * 40 + 20)::numeric
    END as score_total,
    CASE
        WHEN mo_id = 1 THEN 'green'
        WHEN mo_id IN (2,3,4) THEN 'green'
        WHEN mo_id IN (5,6,7,8,9,10,11,12) THEN 'yellow'
        ELSE 'red'
    END as zone
FROM dim_mo mo
CROSS JOIN (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1) p
CROSS JOIN (SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1) v
WHERE EXISTS (SELECT 1 FROM dim_mo WHERE mo_id = mo.mo_id)
ON CONFLICT (mo_id, period_id, version_id) DO UPDATE SET
    score_public = EXCLUDED.score_public,
    score_closed = EXCLUDED.score_closed,
    score_penalties = EXCLUDED.score_penalties,
    score_total = EXCLUDED.score_total,
    zone = EXCLUDED.zone,
    updated_at = CURRENT_TIMESTAMP;

-- Результаты
SELECT COUNT(*) as total_records_created FROM fact_summary
WHERE period_id = (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1);

COMMIT;
