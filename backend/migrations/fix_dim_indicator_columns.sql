-- Fix: Recreate dim_indicator table with missing columns (block_id, criteria_order)
-- This script drops the old table and creates a new one with all columns

BEGIN;

-- Step 1: Drop foreign key constraints that reference dim_indicator
ALTER TABLE fact_indicator DROP CONSTRAINT IF EXISTS fact_indicator_ind_id_fkey;
ALTER TABLE map_scale DROP CONSTRAINT IF EXISTS map_scale_ind_id_fkey;

-- Step 2: Create backup table with old data
CREATE TABLE dim_indicator_backup AS SELECT * FROM dim_indicator;

-- Step 3: Drop old table
DROP TABLE IF EXISTS dim_indicator CASCADE;

-- Step 4: Create new table with all required columns
CREATE TABLE dim_indicator (
    ind_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    block VARCHAR(100),
    block_id INTEGER,
    criteria_order INTEGER,
    description TEXT,
    unit VARCHAR(50),
    is_public BOOLEAN DEFAULT true,
    owner_org VARCHAR(100),
    weight FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 5: Restore data from backup (excluding the new columns)
INSERT INTO dim_indicator (ind_id, code, name, block, description, unit, is_public, owner_org, weight, min_value, max_value, created_at, updated_at)
SELECT ind_id, code, name, block, description, unit, is_public, owner_org, weight, min_value, max_value, created_at, updated_at
FROM dim_indicator_backup;

-- Step 6: Re-add foreign keys
ALTER TABLE fact_indicator ADD CONSTRAINT fact_indicator_ind_id_fkey
    FOREIGN KEY (ind_id) REFERENCES dim_indicator(ind_id);

ALTER TABLE map_scale ADD CONSTRAINT map_scale_ind_id_fkey
    FOREIGN KEY (ind_id) REFERENCES dim_indicator(ind_id);

-- Step 7: Drop backup table
DROP TABLE dim_indicator_backup;

-- Step 8: Verify
SELECT COUNT(*) as indicator_count FROM dim_indicator;
SELECT column_name FROM information_schema.columns WHERE table_name='dim_indicator' ORDER BY ordinal_position;

COMMIT;
