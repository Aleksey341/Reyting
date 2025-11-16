-- Fix: Fill NULL score values from value_raw in fact_indicator table
-- This fixes the issue where imported data shows as 0.00 in the Rating table

BEGIN;

-- Count records with NULL score before fix
SELECT COUNT(*) as null_scores_before FROM fact_indicator WHERE score IS NULL;

-- Update all NULL scores from value_raw
UPDATE fact_indicator
SET score = value_raw
WHERE score IS NULL AND value_raw IS NOT NULL;

-- For records where both are NULL, set to 0
UPDATE fact_indicator
SET score = 0
WHERE score IS NULL;

-- Count records with NULL score after fix
SELECT COUNT(*) as null_scores_after FROM fact_indicator WHERE score IS NULL;

-- Verify the update
SELECT COUNT(*) as total_records,
       COUNT(CASE WHEN score IS NOT NULL THEN 1 END) as with_score,
       COUNT(CASE WHEN score IS NULL THEN 1 END) as without_score
FROM fact_indicator;

COMMIT;
