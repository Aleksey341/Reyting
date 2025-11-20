-- Check 1: Indicators with rating_type
SELECT 'CHECK 1: Indicators by rating_type' as check_name;
SELECT rating_type, COUNT(*) as cnt
FROM dim_indicator
GROUP BY rating_type
ORDER BY rating_type;

-- Check 2: FactIndicator statistics
SELECT '' as blank;
SELECT 'CHECK 2: FactIndicator data statistics' as check_name;
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN score IS NOT NULL THEN 1 END) as with_scores,
    COUNT(CASE WHEN score > 0 THEN 1 END) as positive_scores,
    ROUND(COALESCE(MIN(score), 0)::numeric, 2) as min_score,
    ROUND(COALESCE(MAX(score), 0)::numeric, 2) as max_score,
    ROUND(COALESCE(AVG(score), 0)::numeric, 2) as avg_score
FROM fact_indicator;

-- Check 3: FactSummary records
SELECT '' as blank;
SELECT 'CHECK 3: FactSummary sample (first 10 records)' as check_name;
SELECT 
    mo_id,
    period_id,
    ROUND(COALESCE(score_public, 0)::numeric, 2) as score_public,
    ROUND(COALESCE(score_closed, 0)::numeric, 2) as score_closed,
    ROUND(COALESCE(score_penalties, 0)::numeric, 2) as score_penalties,
    ROUND(COALESCE(score_total, 0)::numeric, 2) as score_total,
    zone
FROM fact_summary
ORDER BY period_id DESC, mo_id
LIMIT 10;

-- Check 4: Manual aggregation test
SELECT '' as blank;
SELECT 'CHECK 4: Manual aggregation test (latest period)' as check_name;

WITH latest_period AS (
    SELECT MAX(period_id) as max_period FROM dim_period
)
SELECT
    'PUBLIC (rating_type=ПУБЛИЧНЫЙ)' as category,
    ROUND(COALESCE(SUM(fi.score), 0)::numeric, 2) as total_score,
    COUNT(fi.fact_ind_id) as count
FROM fact_indicator fi
JOIN dim_indicator di ON fi.ind_id = di.ind_id
WHERE fi.period_id = (SELECT max_period FROM latest_period)
AND di.rating_type = 'ПУБЛИЧНЫЙ'

UNION ALL

SELECT
    'CLOSED (rating_type=ЗАКРЫТЫЙ)' as category,
    ROUND(COALESCE(SUM(fi.score), 0)::numeric, 2) as total_score,
    COUNT(fi.fact_ind_id) as count
FROM fact_indicator fi
JOIN dim_indicator di ON fi.ind_id = di.ind_id
WHERE fi.period_id = (SELECT MAX(period_id) FROM dim_period)
AND di.rating_type = 'ЗАКРЫТЫЙ'

UNION ALL

SELECT
    'PENALTIES (is_penalty=true)' as category,
    ROUND(COALESCE(SUM(fi.score), 0)::numeric, 2) as total_score,
    COUNT(fi.fact_ind_id) as count
FROM fact_indicator fi
JOIN dim_indicator di ON fi.ind_id = di.ind_id
WHERE fi.period_id = (SELECT MAX(period_id) FROM dim_period)
AND di.is_penalty = true;

-- Check 5: Sample indicators
SELECT '' as blank;
SELECT 'CHECK 5: Sample indicators with rating_type' as check_name;
SELECT 
    code,
    LEFT(name, 40) as name,
    COALESCE(rating_type, 'NULL') as rating_type,
    COALESCE(is_penalty::text, 'false') as is_penalty
FROM dim_indicator
WHERE code LIKE 'pub_%' OR code LIKE 'closed_%' OR code LIKE 'pen_%'
ORDER BY code
LIMIT 20;
