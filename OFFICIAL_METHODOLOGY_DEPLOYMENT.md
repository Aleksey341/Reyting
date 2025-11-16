# Official Methodology Implementation - Deployment Guide

## Overview

The official methodology has been fully implemented across the Reyting system. This guide explains what has been done and what needs to happen on Amvera to activate the changes.

**Latest Commits:**
- `6716904`: Initial migration and documentation
- `9933760`: Complete implementation with API endpoints and frontend updates

---

## What Was Implemented

### 1. Database Migration (Auto-executing on app startup)

**File:** `backend/migrations.py` - Function `implement_official_methodology()`

**What it does:**
- Adds 3 new columns to `dim_indicator` table:
  - `rating_type` (VARCHAR): 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ'
  - `is_penalty` (BOOLEAN): TRUE for penalty criteria
  - `max_points` (INTEGER): Variable point values (3-6 for normal, -3 to -5 for penalties)

- Creates **16 official criteria** with proper codes:
  - **PUBLIC (ПУБЛИЧНЫЙ)**: 9 criteria = 31 points max
    - pub_1 to pub_9 with individual max points (3, 5, 3, 3, 3, 3, 3, 3, 3)
  - **CLOSED (ЗАКРЫТЫЙ)**: 8 criteria = 35 points max
    - closed_1 to closed_8 with individual max points (6, 4, 5, 5, 3, 3, 6, 2)
  - **PENALTIES**: 3 criteria that reduce score
    - pen_1 = -3, pen_2 = -3, pen_3 = -5

**When it runs:**
- Automatically on application startup via `backend/main.py`
- Idempotent (safe to run multiple times)
- Only creates criteria if they don't already exist

### 2. SQLAlchemy Models Update

**File:** `backend/models.py` - Class `DimIndicator`

**Changes:**
Added three new Column definitions:
```python
rating_type = Column(String(50))
is_penalty = Column(Boolean, default=False)
max_points = Column(Integer)
```

These fields now reflect the database columns added by the migration.

### 3. New API Endpoints

**File:** `backend/routes/rating_routes_methodology.py`

**New endpoints available at `/api/rating/`:**

#### 1. Get Single Score
```
GET /api/rating/methodology/score/{mo_id}?period_id=1&rating_type=ПУБЛИЧНЫЙ
```
Returns score for one municipality and rating type.

#### 2. Get Comprehensive Rating (Both Public & Closed)
```
GET /api/rating/methodology/comprehensive/{mo_id}?period_id=1
```
Returns both ПУБЛИЧНЫЙ and ЗАКРЫТЫЙ ratings for one municipality.

#### 3. Get All Scores for Period
```
GET /api/rating/methodology/all/{period_id}?rating_type=ПУБЛИЧНЫЙ&sort=score_total&order=desc
```
Returns all municipalities with sorted scores.

#### 4. Risk Zone Reference
```
GET /api/rating/methodology/risk-zones
```
Returns definitions of the three risk zones:
- Зелёная (Green): 53-66 points - High Stability
- Жёлтая (Yellow): 29-52 points - Conditional Stability
- Красная (Red): 0-28 points - Low Stability

#### 5. Methodology Info
```
GET /api/rating/methodology/info
```
Returns complete methodology structure with all criteria definitions.

### 4. Frontend Updates

**File:** `frontend/src/pages/RatingPage.jsx`

**Changes:**
- Updated `blocksConfig` from old structure to official methodology
- Changed from 19 criteria to 16 official criteria
- Added `ratingType` field to blocks (ПУБЛИЧНЫЙ or ЗАКРЫТЫЙ)
- Added `maxPoints` field to each criterion
- Updated all criterion codes to official codes:
  - pub_1, pub_2, ... pub_9 (PUBLIC criteria)
  - closed_1, closed_2, ... closed_8 (CLOSED criteria)
- Updated penalty codes:
  - pen_1, pen_2, pen_3 (replaced pen_01, pen_02, pen_03)

---

## Deployment Steps

### Step 1: Verify Code is on GitHub

All changes have been pushed to the main branch:
```bash
git log --oneline -5
# Should show commit 9933760: "Feat: Complete official methodology..."
```

### Step 2: Deploy/Restart Application on Amvera

The official methodology will activate when the application restarts:

**Option A: Redeploy from GitHub**
1. Go to Amvera dashboard
2. Redeploy the Reyting application (this will pull latest code and restart)

**Option B: Restart Existing Deployment**
1. Go to Amvera dashboard
2. Find the Reyting application
3. Click "Restart" or "Redeploy"

### Step 3: Wait for Migration to Execute

When the app starts, it will:
1. Connect to PostgreSQL
2. Run `run_all_migrations()` from `backend/migrations.py`
3. Execute `implement_official_methodology()` function
4. Create all 16 official criteria in the database
5. Log progress to console

**Expected log output:**
```
[INFO] 🔄 Running migration: Implement official methodology...
[INFO] ✓ Adding methodology-related columns...
[INFO]   ✓ Added rating_type column
[INFO]   ✓ Added is_penalty column
[INFO]   ✓ Added max_points column
[INFO] 🔄 Creating official 16 criteria...
[INFO]   ✓ Created 16 official criteria
```

### Step 4: Verify Migration Success

Check that criteria were created:
```bash
# Connect to Amvera PostgreSQL
# Query the database:
SELECT code, name, rating_type, max_points, is_penalty
FROM dim_indicator
WHERE code IN ('pub_1', 'pub_2', 'closed_1', 'closed_2', 'pen_1')
ORDER BY code;
```

Should return 5 rows (and 11 more if you query all official criteria).

### Step 5: Test API Endpoints

Open the API documentation after deployment:
```
https://reyting-alex1976.amvera.io/api/docs
```

Look for new endpoints under "rating-methodology" tag:
- `/api/rating/methodology/score/{mo_id}` ✅
- `/api/rating/methodology/comprehensive/{mo_id}` ✅
- `/api/rating/methodology/all/{period_id}` ✅
- `/api/rating/methodology/risk-zones` ✅
- `/api/rating/methodology/info` ✅

### Step 6: Test Frontend Display

1. Navigate to the Rating tab in the frontend
2. Verify that:
   - ПУБЛИЧНЫЙ РЕЙТИНГ section displays 9 criteria
   - ЗАКРЫТЫЙ РЕЙТИНГ section displays 8 criteria
   - Penalty columns show п1, п2, п3
   - All scores are displayed correctly

---

## Data Backward Compatibility

### Old vs New Structure

**Old Criteria (being replaced):**
- pm_01 to pm_09 (Political Management)
- ca_01 to ca_04 (Care & Attention)
- dev_01 to dev_03 (Development)
- pen_01 to pen_03 (Penalties)

**New Criteria:**
- pub_1 to pub_9 (PUBLIC rating)
- closed_1 to closed_8 (CLOSED rating)
- pen_1 to pen_3 (Penalties)

### Migration Strategy

The migration is **additive** - it:
1. Preserves existing `fact_indicator` data
2. Creates new criteria alongside old ones
3. Does NOT delete old criteria automatically
4. Allows gradual migration of scores

**Important:** You may need to manually migrate old scores to new criteria codes, or update data import scripts to use the new official codes.

---

## Verification Checklist

After deployment, verify:

- [ ] Application deployed successfully to Amvera
- [ ] Migration executed (check logs for "Created 16 official criteria")
- [ ] Database shows new columns: rating_type, is_penalty, max_points
- [ ] Database shows 16 official criteria with new codes
- [ ] API endpoints respond with correct structure
- [ ] Frontend displays ПУБЛИЧНЫЙ and ЗАКРЫТЫЙ sections
- [ ] Scores are visible in Rating tab
- [ ] Risk zones are calculated correctly

---

## Troubleshooting

### Problem: Migration didn't execute
**Solution:** Check application logs in Amvera. If migration failed:
1. Check database connection string in environment
2. Verify PostgreSQL database is accessible
3. Check for permission errors
4. Manually run migration SQL from `backend/migrations/implement_official_methodology.sql`

### Problem: Old and new criteria both visible
**Solution:** This is expected. You can either:
1. Keep both for transition period
2. Clean up old criteria manually if no data references them
3. Create a data migration to map old scores to new criteria

### Problem: Frontend not showing new criteria
**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
2. Hard refresh (Ctrl+F5 or Cmd+Shift+R)
3. Check that frontend code was updated (git pull)
4. Check browser console for errors (F12)

---

## API Response Examples

### Example 1: Get Methodology Score
```bash
curl "https://reyting-alex1976.amvera.io/api/rating/methodology/score/1?period_id=1&rating_type=ПУБЛИЧНЫЙ"
```

Response:
```json
{
  "mo_id": 1,
  "mo_name": "Липецк",
  "leader_name": "Иванов И.И.",
  "rating_type": "ПУБЛИЧНЫЙ",
  "period_id": 1,
  "public_score": 25.5,
  "penalties": -2.0,
  "subtotal": 25.5,
  "total_score": 23.5,
  "risk_zone": "Жёлтая",
  "risk_status": "Conditional Stability",
  "blocks": [
    {
      "block_name": "Политический менеджмент",
      "rating_type": "ПУБЛИЧНЫЙ",
      "max_points": 14,
      "score": 10.5,
      "percentage": 75.0,
      "criteria_count": 4,
      "criteria": [...]
    }
  ]
}
```

### Example 2: Get Risk Zones
```bash
curl "https://reyting-alex1976.amvera.io/api/rating/methodology/risk-zones"
```

Response:
```json
{
  "zones": [
    {
      "zone_name": "Зелёная",
      "score_range": "53-66",
      "status": "High Stability",
      "color": "green"
    },
    {
      "zone_name": "Жёлтая",
      "score_range": "29-52",
      "status": "Conditional Stability",
      "color": "yellow"
    },
    {
      "zone_name": "Красная",
      "score_range": "0-28",
      "status": "Low Stability",
      "color": "red"
    }
  ]
}
```

---

## Next Steps

After verifying the implementation works:

1. **Data Migration:** Migrate old indicator scores to new criteria codes
2. **Documentation Update:** Update user guides and API documentation
3. **Testing:** Conduct user acceptance testing with real data
4. **Feedback:** Gather feedback from stakeholders about the new methodology display

---

## References

- **Official Methodology Document:** "Методика оценки эффективности деятельности глав администраций МО 23.10.pdf"
- **Implementation Doc:** `OFFICIAL_METHODOLOGY_IMPLEMENTATION.md`
- **Database Migration:** `backend/migrations.py` (function `implement_official_methodology`)
- **API Routes:** `backend/routes/rating_routes_methodology.py`
- **Frontend:** `frontend/src/pages/RatingPage.jsx`

---

## Support

For questions or issues with the official methodology implementation:
1. Check Amvera application logs
2. Review this deployment guide
3. Check `OFFICIAL_METHODOLOGY_IMPLEMENTATION.md` for technical details
4. Review the API documentation at `/api/docs`
