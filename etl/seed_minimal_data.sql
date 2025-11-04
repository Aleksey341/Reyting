-- Seed minimal data for development and testing
-- This script populates basic reference data to ensure API returns non-empty responses

BEGIN;

-- 1. Insert methodology version (if not exists)
INSERT INTO dim_methodology (version, valid_from, notes)
VALUES ('v1.0', CURRENT_DATE, 'Первичная версия методики')
ON CONFLICT (version) DO NOTHING;

-- 2. Insert sample indicator (public data)
INSERT INTO dim_indicator (code, name, block, description, unit, is_public, owner_org, weight, min_value, max_value)
VALUES ('POP', 'Численность населения', 'Демография', 'Население МО, чел.', 'чел', true, 'Статистика', 1.0, 0, 10000000)
ON CONFLICT (code) DO NOTHING;

-- 3. Insert sample penalty
INSERT INTO dim_penalty (code, name, description, owner_org)
VALUES ('P01', 'Штраф за просроченные отчёты', 'Формальный штрафной балл', 'Администратор')
ON CONFLICT (code) DO NOTHING;

-- 4. Insert sample municipality
INSERT INTO dim_mo (mo_name, oktmo, okato, lat, lon, type, population, area_km2)
VALUES ('Город N', '18000000', '18000', 57.6261, 39.8845, 'город', 600000, 205.0)
ON CONFLICT (mo_name) DO NOTHING;

-- 5. Insert current month period
INSERT INTO dim_period (period_type, date_from, date_to, edg_flag)
SELECT 'month',
       DATE_TRUNC('month', CURRENT_DATE)::date,
       (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day')::date,
       false
WHERE NOT EXISTS (
    SELECT 1 FROM dim_period
    WHERE period_type = 'month'
    AND date_from = DATE_TRUNC('month', CURRENT_DATE)::date
);

-- 6. Insert map scale configuration for sample indicator
WITH m AS (SELECT version_id FROM dim_methodology WHERE version='v1.0'),
     i AS (SELECT ind_id FROM dim_indicator WHERE code='POP')
INSERT INTO map_scale (version_id, ind_id, zone, min_score, max_score, color_hex)
SELECT m.version_id, i.ind_id, z.zone, z.min_score, z.max_score, z.color_hex
FROM m, i, (VALUES
  ('A', 0.00,   0.25, '#2E7D32'),
  ('B', 0.25, 0.50, '#558B2F'),
  ('C', 0.50, 0.75, '#F9A825'),
  ('D', 0.75, 1.00, '#C62828')
) AS z(zone, min_score, max_score, color_hex)
WHERE NOT EXISTS (
    SELECT 1 FROM map_scale ms
    WHERE ms.version_id = m.version_id
    AND ms.ind_id = i.ind_id
);

-- 7. Insert sample fact_indicator record
WITH mo AS (SELECT mo_id FROM dim_mo WHERE mo_name='Город N'),
     p  AS (SELECT period_id FROM dim_period WHERE period_type='month' ORDER BY period_id DESC LIMIT 1),
     i  AS (SELECT ind_id FROM dim_indicator WHERE code='POP'),
     v  AS (SELECT version_id FROM dim_methodology WHERE version='v1.0')
INSERT INTO fact_indicator (mo_id, period_id, ind_id, version_id, value_raw, value_norm, score, target)
SELECT mo.mo_id, p.period_id, i.ind_id, v.version_id, 600000, 0.6, 0.6, 700000
FROM mo, p, i, v
ON CONFLICT (mo_id, period_id, ind_id, version_id) DO NOTHING;

-- 8. Insert sample fact_summary record
WITH mo AS (SELECT mo_id FROM dim_mo WHERE mo_name='Город N'),
     p  AS (SELECT period_id FROM dim_period WHERE period_type='month' ORDER BY period_id DESC LIMIT 1),
     v  AS (SELECT version_id FROM dim_methodology WHERE version='v1.0')
INSERT INTO fact_summary (mo_id, period_id, version_id, score_public, score_closed, score_penalties, score_total, zone)
SELECT mo.mo_id, p.period_id, v.version_id, 0.6, 0.0, 0.0, 0.6, 'B'
FROM mo, p, v
ON CONFLICT (mo_id, period_id, version_id) DO NOTHING;

COMMIT;

-- Verify seed data
SELECT 'Methodology versions' as section, COUNT(*) as count FROM dim_methodology
UNION ALL
SELECT 'Indicators', COUNT(*) FROM dim_indicator
UNION ALL
SELECT 'Penalties', COUNT(*) FROM dim_penalty
UNION ALL
SELECT 'Municipalities', COUNT(*) FROM dim_mo
UNION ALL
SELECT 'Periods', COUNT(*) FROM dim_period
UNION ALL
SELECT 'Map scales', COUNT(*) FROM map_scale
UNION ALL
SELECT 'Fact indicators', COUNT(*) FROM fact_indicator
UNION ALL
SELECT 'Fact summaries', COUNT(*) FROM fact_summary;
