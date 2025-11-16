-- Migration: Add leader_name column to dim_mo table
-- Purpose: Store the name (ФИО) of the municipal leader (глава МО)
-- Created: 2024

BEGIN;

-- Add leader_name column to dim_mo table
ALTER TABLE dim_mo
ADD COLUMN leader_name VARCHAR(255);

-- Add comment to the column
COMMENT ON COLUMN dim_mo.leader_name IS 'ФИО главы муниципального образования';

-- Create index for faster queries by leader name
CREATE INDEX idx_dim_mo_leader_name ON dim_mo(leader_name);

COMMIT;
