-- Check what indicator codes exist in the database
SELECT ind_id, code, name, block FROM dim_indicator ORDER BY ind_id LIMIT 30;
