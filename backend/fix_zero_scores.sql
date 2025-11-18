-- FIX: Zero Rating Scores
-- This script ensures rating_type is set on all official methodology indicators
-- and recalculates aggregated scores

BEGIN TRANSACTION;

-- STEP 1: Ensure rating_type is set on all official indicators
UPDATE dim_indicator
SET rating_type = 'ПУБЛИЧНЫЙ'
WHERE code LIKE 'pub_%' AND rating_type IS NULL;

UPDATE dim_indicator
SET rating_type = 'ЗАКРЫТЫЙ'
WHERE code LIKE 'closed_%' AND rating_type IS NULL;

UPDATE dim_indicator
SET is_penalty = TRUE
WHERE code LIKE 'pen_%' AND is_penalty = FALSE;

-- STEP 2: Clear existing FactSummary (we'll recalculate)
DELETE FROM fact_summary;

-- STEP 3: Recalculate FactSummary from FactIndicator
INSERT INTO fact_summary (mo_id, period_id, version_id, score_public, score_closed, score_penalties, score_total, zone, updated_at)
WITH aggregated AS (
    SELECT
        fi.mo_id,
        fi.period_id,
        COALESCE(SUM(CASE WHEN di.rating_type = 'ПУБЛИЧНЫЙ' THEN fi.score ELSE 0 END), 0) as score_public,
        COALESCE(SUM(CASE WHEN di.rating_type = 'ЗАКРЫТЫЙ' THEN fi.score ELSE 0 END), 0) as score_closed,
        COALESCE(SUM(CASE WHEN di.is_penalty = TRUE THEN fi.score ELSE 0 END), 0) as score_penalties
    FROM fact_indicator fi
    JOIN dim_indicator di ON fi.ind_id = di.ind_id
    WHERE fi.score IS NOT NULL
    GROUP BY fi.mo_id, fi.period_id
)
SELECT
    mo_id,
    period_id,
    1 as version_id,
    score_public,
    score_closed,
    score_penalties,
    GREATEST(0.0, score_public + score_closed + score_penalties) as score_total,
    CASE
        WHEN GREATEST(0.0, score_public + score_closed + score_penalties) >= 53 THEN 'Зелёная'
        WHEN GREATEST(0.0, score_public + score_closed + score_penalties) >= 29 THEN 'Жёлтая'
        ELSE 'Красная'
    END as zone,
    NOW() as updated_at
FROM aggregated;

COMMIT;

-- Verify the fix
SELECT '=== VERIFICATION ===' as title;
SELECT 'Indicators by rating_type:' as check_name;
SELECT rating_type, COUNT(*) as cnt FROM dim_indicator GROUP BY rating_type ORDER BY rating_type;

SELECT '' as blank;
SELECT 'FactSummary sample (top 10):' as check_name;
SELECT mo_id, period_id, score_public, score_closed, score_penalties, score_total, zone
FROM fact_summary
ORDER BY period_id DESC, score_total DESC
LIMIT 10;
