# Fix: Zero Rating Scores After Data Import

## Problem

After uploading Excel file with methodology data:
- Data imports successfully (360 indicator values loaded)
- FactSummary records are created
- BUT all scores show as 0 in the rating table
- Reyting dashboard displays empty ratings

## Root Cause

The rating aggregation system groups scores by `rating_type`:
- **PUBLIC criteria** (pub_1 to pub_9): `rating_type = 'ПУБЛИЧНЫЙ'`
- **CLOSED criteria** (closed_1 to closed_8): `rating_type = 'ЗАКРЫТЫЙ'`
- **PENALTY criteria** (pen_1 to pen_3): `is_penalty = TRUE`

If indicators don't have proper `rating_type` set, the SQL aggregation queries return NULL/0 because:
```sql
SELECT SUM(fi.score)
FROM fact_indicator fi
JOIN dim_indicator di ON fi.ind_id = di.ind_id
WHERE di.rating_type = 'ПУБЛИЧНЫЙ'  -- Returns 0 if no indicators match this
```

## Solution

Execute the SQL fix script to:
1. Set `rating_type` on all existing indicators matching the code pattern
2. Clear corrupted FactSummary records
3. Recalculate aggregated scores correctly

### Option 1: Using psql (Recommended)

```bash
# Connect to database and execute fix script
psql $DATABASE_URL < backend/fix_zero_scores.sql

# Or if DATABASE_URL is not set:
psql -U reyting_user -d reytingdb -h localhost -f backend/fix_zero_scores.sql
```

### Option 2: Using Python Script

```bash
# Install dependencies if needed
pip install sqlalchemy psycopg2-binary python-dotenv

# Run the Python fix script
python3 backend/fix_rating_scores.py
```

### Option 3: Manual SQL

If you have direct database access, execute these commands in order:

```sql
-- 1. Ensure rating_type is set on public criteria
UPDATE dim_indicator
SET rating_type = 'ПУБЛИЧНЫЙ'
WHERE code LIKE 'pub_%' AND rating_type IS NULL;

-- 2. Ensure rating_type is set on closed criteria
UPDATE dim_indicator
SET rating_type = 'ЗАКРЫТЫЙ'
WHERE code LIKE 'closed_%' AND rating_type IS NULL;

-- 3. Ensure is_penalty is set on penalty criteria
UPDATE dim_indicator
SET is_penalty = TRUE
WHERE code LIKE 'pen_%' AND is_penalty = FALSE;

-- 4. Clear corrupted aggregates
DELETE FROM fact_summary;

-- 5. Recalculate aggregates correctly
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
```

## Verification

After running the fix, check that scores are now calculated correctly:

```bash
# Using psql
psql $DATABASE_URL << EOF
SELECT 'Indicators by rating_type:' as check;
SELECT rating_type, COUNT(*) as count FROM dim_indicator GROUP BY rating_type;

SELECT '' as blank;
SELECT 'FactSummary sample:' as check;
SELECT mo_id, period_id, score_public, score_closed, score_penalties, score_total, zone
FROM fact_summary LIMIT 10;
EOF
```

Expected output:
```
 rating_type │ count
─────────────┼───────
 ЗАКРЫТЫЙ    │     8
 ПУБЛИЧНЫЙ   │     9
 (null)      │   ...
(3 rows)

 mo_id │ period_id │ score_public │ score_closed │ score_penalties │ score_total │   zone
───────┼───────────┼──────────────┼──────────────┼─────────────────┼─────────────┼──────────────
     1 │        27 │           15 │           18 │            -2   │          31 │ Жёлтая
     2 │        27 │           18 │           15 │             0   │          33 │ Жёлтая
     3 │        27 │           12 │           14 │            -1   │          25 │ Красная
```

## Frontend Update

After the database fix:

1. **Hard refresh** the dashboard (Ctrl+F5 or Cmd+Shift+R)
2. The `/api/rating` endpoint will now return proper scores
3. Ratings should display with correct scores and color zones

## Files Modified

- `backend/fix_zero_scores.sql` - SQL script for database fix
- `backend/fix_rating_scores.py` - Python alternative fix script

## Technical Details

### Score Calculation Formula

```
score_public = SUM(all indicators where rating_type = 'ПУБЛИЧНЫЙ')
score_closed = SUM(all indicators where rating_type = 'ЗАКРЫТЫЙ')
score_penalties = SUM(all indicators where is_penalty = TRUE)
score_total = MAX(0, score_public + score_closed + score_penalties)

zone determination:
  - if score_total >= 53: 'Зелёная' (Green)
  - if score_total >= 29: 'Жёлтая' (Yellow)
  - else: 'Красная' (Red)
```

### Indicator Classification

The official methodology has 20 total criteria:

**PUBLIC (9 criteria):** `pub_1` to `pub_9`
- pub_1: Поддержка руководства области
- pub_2: Выполнение задач АГП
- pub_3: Позиционирование главы МО
- pub_4: Проектная деятельность
- pub_5: Вовлеченность молодежи (Добровольчество)
- pub_6: Вовлеченность молодежи (Движение Первых)
- pub_8: Кадровый управленческий резерв
- pub_9: Работа с грантами

**CLOSED (8 criteria):** `closed_1` to `closed_8`
- closed_1: Партийная принадлежность сотрудников
- closed_2: Распределение мандатов
- closed_3: Показатели АГП (Уровень)
- closed_4: Показатели АГП (Качество)
- closed_5: Экономическая привлекательность
- closed_6: Личная работа главы с ветеранами
- closed_7: Партийная принадлежность ветеранов
- closed_8: Участие в проекте «Гордость Липецкой области»

**PENALTIES (3 criteria):** `pen_1` to `pen_3`
- pen_1: Конфликты с региональной властью (negative)
- pen_2: Внутримуниципальные конфликты (negative)
- pen_3: Данные правоохранительных органов (negative)

## Prevention

To prevent this issue in the future:

1. **At startup**: Ensure `implement_official_methodology()` migration runs first
2. **During import**: Verify that indicators are properly linked by code (pub_*, closed_*, pen_*)
3. **After import**: Check that scores are non-zero before releasing

Add this check to the import process:

```python
# After import, verify aggregation worked
result = session.execute(text("""
    SELECT COUNT(*) FROM fact_summary
    WHERE score_total > 0
"""))
if result.scalar() == 0:
    raise Exception("ERROR: Aggregation failed - no scores calculated!")
```

## Questions?

- Check the database schema in `database_schema.sql`
- Review the aggregation logic in `migrations.py::calculate_fact_summary_from_indicators()`
- Check import logic in `routes/data_import_routes.py::import_official_methodology_excel()`
