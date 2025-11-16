-- SQL скрипт для заполнения БД данными для вкладки "Рейтинг"
-- Создает тестовые данные с баллами за критерии и штрафы
-- Дата: 16 ноября 2024

BEGIN;

-- ============================================================================
-- 1. УБЕДИТЬСЯ ЧТО ЕСТЬ ПЕРИОД 2024-01
-- ============================================================================

INSERT INTO dim_period (period_type, date_from, date_to, edg_flag)
SELECT 'month', '2024-01-01'::date, '2024-01-31'::date, false
WHERE NOT EXISTS (
    SELECT 1 FROM dim_period
    WHERE date_from = '2024-01-01'::date AND date_to = '2024-01-31'::date
);

-- Получить ID периода для использования
WITH period_info AS (
    SELECT period_id FROM dim_period
    WHERE date_from = '2024-01-01'::date AND date_to = '2024-01-31'::date
    LIMIT 1
)

-- ============================================================================
-- 2. СОЗДАТЬ/ОБНОВИТЬ МЕТОДИКУ v1.0
-- ============================================================================

INSERT INTO dim_methodology (version, valid_from, valid_to, notes)
SELECT 'v1.0', CURRENT_DATE, NULL, 'Базовая версия методики рейтинга'
WHERE NOT EXISTS (SELECT 1 FROM dim_methodology WHERE version = 'v1.0')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 3. СОЗДАТЬ ПОКАЗАТЕЛИ (КРИТЕРИИ) 1-17
-- ============================================================================

-- Удалим старые индикаторы для примера (если нужно)
-- DELETE FROM dim_indicator WHERE code LIKE '%';

-- Добавляем 17 критериев для примера
INSERT INTO dim_indicator (code, name, block, unit, is_public, weight, min_value, max_value)
VALUES
    ('1', 'Критерий 1', 'Управление', 'балл', true, 1.0, 0, 5),
    ('2', 'Критерий 2', 'Управление', 'балл', true, 1.0, 0, 5),
    ('3', 'Критерий 3', 'Управление', 'балл', true, 1.0, 0, 5),
    ('4', 'Критерий 4', 'Экономика', 'балл', true, 1.0, 0, 5),
    ('5', 'Критерий 5', 'Экономика', 'балл', true, 1.0, 0, 5),
    ('6', 'Критерий 6', 'Экономика', 'балл', true, 1.0, 0, 5),
    ('7', 'Критерий 7', 'Социал', 'балл', true, 1.0, 0, 5),
    ('8', 'Критерий 8', 'Социал', 'балл', true, 1.0, 0, 5),
    ('9', 'Критерий 9', 'Инфраструктура', 'балл', true, 1.0, 0, 5),
    ('10', 'Критерий 10', 'Инфраструктура', 'балл', true, 1.0, 0, 5),
    ('11', 'Критерий 11', 'Инфраструктура', 'балл', true, 1.0, 0, 5),
    ('12', 'Критерий 12', 'Образование', 'балл', true, 1.0, 0, 5),
    ('13', 'Критерий 13', 'Образование', 'балл', true, 1.0, 0, 5),
    ('14', 'Критерий 14', 'Здравоохр', 'балл', true, 1.0, 0, 5),
    ('15', 'Критерий 15', 'Здравоохр', 'балл', true, 1.0, 0, 5),
    ('16', 'Критерий 16', 'Здравоохр', 'балл', true, 1.0, 0, 5),
    ('17', 'Критерий 17', 'Культура', 'балл', true, 1.0, 0, 5)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 4. СОЗДАТЬ ШТРАФЫ (ПАРАМЕТРЫ 18-21)
-- ============================================================================

INSERT INTO dim_penalty (code, name, description)
VALUES
    ('penalty_18', 'Штраф 18', 'Нарушение в отчетности'),
    ('penalty_19', 'Штраф 19', 'Задержка в реализации программ'),
    ('penalty_20', 'Штраф 20', 'Конфликты с общественностью'),
    ('penalty_21', 'Штраф 21', 'Нарушение бюджетной дисциплины')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- 5. ОЧИСТИТЬ СТАРЫЕ ДАННЫЕ И ЗАПОЛНИТЬ НОВЫЕ FACT_INDICATOR
-- ============================================================================

WITH period_data AS (
    SELECT period_id FROM dim_period
    WHERE date_from = '2024-01-01'::date
    LIMIT 1
),
version_data AS (
    SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1
),
mo_list AS (
    SELECT mo_id FROM dim_mo ORDER BY mo_id
)
DELETE FROM fact_indicator
WHERE period_id IN (SELECT period_id FROM period_data)
  AND version_id IN (SELECT version_id FROM version_data);

-- Заполнить fact_indicator с баллами за каждый критерий по каждому МО
INSERT INTO fact_indicator (mo_id, period_id, ind_id, version_id, value_raw, value_norm, score)
SELECT
    mo.mo_id,
    p.period_id,
    i.ind_id,
    v.version_id,
    CASE
        -- Липецк - максимальные баллы
        WHEN mo.mo_name = 'Липецк' THEN CASE
            WHEN i.code IN ('1','2','3','8','12') THEN 3
            WHEN i.code IN ('4','5','6','7','9','13','14','15','16','17') THEN 5
            ELSE 3
        END
        -- Елец - хорошие баллы
        WHEN mo.mo_name = 'Елец' THEN CASE
            WHEN i.code IN ('1','2','3','8','12','14','15','16','17') THEN 3
            WHEN i.code IN ('4','5','6','7','9','10','11','13') THEN 4
            ELSE 3
        END
        -- Воловский
        WHEN mo.mo_name = 'Воловский' THEN CASE
            WHEN i.code IN ('1','2','3','8','12','14','15','16','17') THEN 3
            WHEN i.code IN ('4','5','6','7','9','10','11','13') THEN 4
            ELSE 3
        END
        -- Грязянский
        WHEN mo.mo_name = 'Грязинский' THEN CASE
            WHEN i.code IN ('1','2','3','8','12','14','15','16','17') THEN 3
            WHEN i.code IN ('4','5','6','7','9','10','11','13') THEN 4
            ELSE 1
        END
        -- Данковский - средние баллы
        WHEN mo.mo_name = 'Данковский' THEN CASE
            WHEN i.code IN ('1','2','3','8','9','10','11','12','13') THEN 3
            WHEN i.code IN ('4','5','6','7') THEN 4
            ELSE 0
        END
        -- Добринский - низкие баллы
        WHEN mo.mo_name = 'Добринский' THEN CASE
            WHEN i.code IN ('1','2','3','8') THEN 3
            ELSE 1
        END
        -- Добровский
        WHEN mo.mo_name = 'Добровский' THEN CASE
            WHEN i.code IN ('1','2','3','8') THEN 3
            WHEN i.code IN ('4','5','6','7') THEN 3
            ELSE 1
        END
        -- Долгоруковский
        WHEN mo.mo_name = 'Долгоруковский' THEN CASE
            WHEN i.code IN ('1','2','3','8') THEN 3
            WHEN i.code IN ('4','5','6','7','10','11') THEN 1
            ELSE 1
        END
        -- Остальные МО - низкие баллы
        ELSE CASE WHEN i.code IN ('1','2','3','8') THEN 3 ELSE 1 END
    END::numeric as value_raw,
    CASE
        WHEN mo.mo_name = 'Липецк' THEN 0.9
        WHEN mo.mo_name IN ('Елец', 'Воловский') THEN 0.8
        WHEN mo.mo_name IN ('Грязинский', 'Данковский') THEN 0.7
        ELSE 0.5
    END::numeric as value_norm,
    CASE
        WHEN mo.mo_name = 'Липецк' THEN 5
        WHEN mo.mo_name IN ('Елец', 'Воловский') THEN 4
        WHEN mo.mo_name IN ('Грязинский') THEN 3
        WHEN mo.mo_name IN ('Данковский', 'Добринский') THEN 2
        ELSE 1
    END::numeric as score
FROM dim_mo mo
CROSS JOIN (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1) p
CROSS JOIN (SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1) v
CROSS JOIN dim_indicator i
WHERE mo.mo_name IS NOT NULL
ON CONFLICT (mo_id, period_id, ind_id, version_id) DO UPDATE SET
    value_raw = EXCLUDED.value_raw,
    value_norm = EXCLUDED.value_norm,
    score = EXCLUDED.score;

-- ============================================================================
-- 6. ОЧИСТИТЬ И ЗАПОЛНИТЬ FACT_PENALTY
-- ============================================================================

WITH period_data AS (
    SELECT period_id FROM dim_period
    WHERE date_from = '2024-01-01'::date
    LIMIT 1
),
version_data AS (
    SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1
)
DELETE FROM fact_penalty
WHERE period_id IN (SELECT period_id FROM period_data)
  AND version_id IN (SELECT version_id FROM version_data);

-- Добавить штрафы
INSERT INTO fact_penalty (mo_id, period_id, pen_id, version_id, score_negative, details)
SELECT
    mo.mo_id,
    p.period_id,
    pen.pen_id,
    v.version_id,
    CASE
        -- Липецк - 1 штраф на -1
        WHEN mo.mo_name = 'Липецк' AND pen.code = 'penalty_19' THEN -1
        -- Елец - 2 штрафа на -1 каждый
        WHEN mo.mo_name = 'Елец' AND pen.code IN ('penalty_19', 'penalty_20') THEN -1
        -- Воловский - 2 штрафа
        WHEN mo.mo_name = 'Воловский' AND pen.code IN ('penalty_19', 'penalty_20') THEN -1
        -- Грязинский - 1 штраф
        WHEN mo.mo_name = 'Грязинский' AND pen.code = 'penalty_19' THEN -1
        -- Данковский - 1 штраф
        WHEN mo.mo_name = 'Данковский' AND pen.code = 'penalty_19' THEN -1
        -- Добринский - 1 штраф
        WHEN mo.mo_name = 'Добринский' AND pen.code = 'penalty_19' THEN -1
        -- Добровский - 1 штраф
        WHEN mo.mo_name = 'Добровский' AND pen.code = 'penalty_19' THEN -1
        -- Долгоруковский - 0 штрафов
        -- Остальные - нет штрафов
        ELSE 0
    END::numeric as score_negative,
    CASE
        WHEN mo.mo_name = 'Липецк' AND pen.code = 'penalty_19' THEN 'Небольшая задержка'
        WHEN mo.mo_name = 'Елец' AND pen.code = 'penalty_19' THEN 'Задержка в реализации'
        WHEN mo.mo_name = 'Елец' AND pen.code = 'penalty_20' THEN 'Конфликт с общественностью'
        WHEN pen.code = 'penalty_19' THEN 'Задержка в программах'
        ELSE NULL
    END as details
FROM dim_mo mo
CROSS JOIN (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1) p
CROSS JOIN (SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1) v
CROSS JOIN dim_penalty pen
WHERE mo.mo_name IS NOT NULL
  AND (
    (mo.mo_name = 'Липецк' AND pen.code = 'penalty_19')
    OR (mo.mo_name = 'Елец' AND pen.code IN ('penalty_19', 'penalty_20'))
    OR (mo.mo_name = 'Воловский' AND pen.code IN ('penalty_19', 'penalty_20'))
    OR (mo.mo_name IN ('Грязинский', 'Данковский', 'Добринский', 'Добровский') AND pen.code = 'penalty_19')
  )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 7. ЗАПОЛНИТЬ FACT_SUMMARY - САМОЕ ВАЖНОЕ ДЛЯ РЕЙТИНГА
-- ============================================================================

WITH period_data AS (
    SELECT period_id FROM dim_period
    WHERE date_from = '2024-01-01'::date
    LIMIT 1
),
version_data AS (
    SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1
)
DELETE FROM fact_summary
WHERE period_id IN (SELECT period_id FROM period_data)
  AND version_id IN (SELECT version_id FROM version_data);

-- Вычислить итоговые баллы на основе реальной методики
INSERT INTO fact_summary (mo_id, period_id, version_id, score_public, score_closed, score_penalties, score_total, zone)
SELECT
    mo.mo_id,
    p.period_id,
    v.version_id,

    -- Баллы за публичные критерии (1-13)
    COALESCE(
        (SELECT SUM(score) FROM fact_indicator
         WHERE mo_id = mo.mo_id
         AND period_id = p.period_id
         AND version_id = v.version_id
         AND ind_id IN (SELECT ind_id FROM dim_indicator WHERE code IN ('1','2','3','4','5','6','7','8','9','10','11','12','13'))
        ),
        0
    )::numeric(6,2) as score_public,

    -- Баллы за закрытые критерии (14-17)
    COALESCE(
        (SELECT SUM(score) FROM fact_indicator
         WHERE mo_id = mo.mo_id
         AND period_id = p.period_id
         AND version_id = v.version_id
         AND ind_id IN (SELECT ind_id FROM dim_indicator WHERE code IN ('14','15','16','17'))
        ),
        0
    )::numeric(6,2) as score_closed,

    -- Штрафные баллы
    COALESCE(
        (SELECT SUM(score_negative) FROM fact_penalty
         WHERE mo_id = mo.mo_id
         AND period_id = p.period_id
         AND version_id = v.version_id
        ),
        0
    )::numeric(6,2) as score_penalties,

    -- ИТОГОВЫЙ БАЛЛ
    ROUND(
        COALESCE((SELECT SUM(score) FROM fact_indicator WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0)
        + COALESCE((SELECT SUM(score_negative) FROM fact_penalty WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0),
        0
    )::numeric(6,2) as score_total,

    -- ЗОНА (на основе итогового балла)
    CASE
        WHEN ROUND(COALESCE((SELECT SUM(score) FROM fact_indicator WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0)
                 + COALESCE((SELECT SUM(score_negative) FROM fact_penalty WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0), 0) >= 53 THEN 'green'
        WHEN ROUND(COALESCE((SELECT SUM(score) FROM fact_indicator WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0)
                 + COALESCE((SELECT SUM(score_negative) FROM fact_penalty WHERE mo_id = mo.mo_id AND period_id = p.period_id AND version_id = v.version_id), 0), 0) >= 29 THEN 'yellow'
        ELSE 'red'
    END as zone

FROM dim_mo mo
CROSS JOIN (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1) p
CROSS JOIN (SELECT version_id FROM dim_methodology WHERE version = 'v1.0' LIMIT 1) v
WHERE mo.mo_name IS NOT NULL
ON CONFLICT (mo_id, period_id, version_id) DO UPDATE SET
    score_public = EXCLUDED.score_public,
    score_closed = EXCLUDED.score_closed,
    score_penalties = EXCLUDED.score_penalties,
    score_total = EXCLUDED.score_total,
    zone = EXCLUDED.zone;

-- ============================================================================
-- 8. ПРОВЕРКА - ВЫВЕСТИ РЕЗУЛЬТАТЫ
-- ============================================================================

-- Показать созданный рейтинг
SELECT
    mo.mo_name,
    mo.leader_name,
    s.score_public,
    s.score_closed,
    s.score_penalties,
    s.score_total,
    s.zone
FROM fact_summary s
JOIN dim_mo mo ON s.mo_id = mo.mo_id
WHERE s.period_id = (SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'::date LIMIT 1)
ORDER BY s.score_total DESC;

COMMIT;
