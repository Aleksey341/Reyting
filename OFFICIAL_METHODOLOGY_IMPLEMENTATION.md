# Official Methodology Implementation Guide

## Overview

This document describes the implementation of the official methodology for rating municipal heads ("Методика оценки эффективности деятельности глав администраций МО") in the Reyting system.

**Document Source:** "Методика оценки глав мо 23.10.pdf"
**Status:** Implementation in progress
**Last Updated:** November 16, 2025

---

## Methodology Summary

### Criteria Structure

The official methodology defines **16 criteria** organized into two rating types:

#### ПУБЛИЧНЫЙ РЕЙТИНГ (PUBLIC Rating) - 31 Points Maximum

**Block 1: Political Management (Политический менеджмент)** - 14 points
1. `pub_1` - Поддержка руководства области (3 pts)
   - Support from regional leadership (Governor, deputies, ministers)
   - Scoring: 0-3 based on level of support

2. `pub_2` - Выполнение задач АГП (5 pts)
   - Effectiveness of AGP (Government Apparatus) tasks execution
   - Scoring: 91-100% = 5 pts, 81-90% = 4 pts, 71-80% = 3 pts, 61-70% = 2 pts, 51-60% = 1 pt, <50% = 0 pts

3. `pub_3` - Позиционирование главы МО (3 pts)
   - Unique positioning of municipality head
   - Scoring: Functional/entrepreneur = 3 pts, Blurred = 0 pts

4. `pub_4` - Проектная деятельность главы (3 pts)
   - Project activity of the head
   - Scoring: 1+ regional & 1+ municipal = 3 pts, 1 regional = 2 pts, 1 municipal = 1 pt, None = 0 pts

**Block 2: Care & Attention (Забота и внимание)** - 9 points
5. `pub_5` - Молодежь в добровольчестве (3 pts)
   - Youth involvement in volunteering
   - Scoring: >50% = 3 pts, 26-50% = 2 pts, 16-25% = 1 pt, <15% = 0 pts

6. `pub_6` - Молодежь в Движении Первых (3 pts)
   - Youth participation in "Movement of the Firsts"
   - Scoring: >50% = 3 pts, 26-50% = 2 pts, 16-25% = 1 pt, <15% = 0 pts

7. `pub_7` - Работа с ветеранами СВО (3 pts)
   - Personal involvement with SVO (Special Military Operation) veterans
   - Scoring: ≥36 meetings/year & ≥80% participation = 3 pts, 12-35 meetings & ≥40% = 2 pts, 3-11 meetings & ≤20% = 1 pt, <2 meetings = 0 pts

**Block 3: Development of Cadres & Projects (Развитие кадрового потенциала)** - 8 points
8. `pub_8` - Кадровый управленческий резерв (3 pts)
   - Development of management cadre reserve
   - Scoring: 80-100% positions = 3 pts, 50-79% = 2 pts, 30-49% = 1 pt, <30% = 0 pts

9. `pub_9` - Работа с грантами (3 pts)
   - Effectiveness with federal/regional grants
   - Scoring: 3+ consecutive wins or ≥10M rubles = 3 pts, 1-2 wins or ≥1M rubles = 1 pt, None = 0 pts

**PUBLIC TOTAL: 9 criteria = 31 points**

---

#### ЗАКРЫТЫЙ РЕЙТИНГ (CLOSED Rating) - 35 Points Maximum

**Block 1: Political Management** - 23 points
10. `closed_1` - Партийное мнение в администрации (6 pts)
    - Party opinion in administration (members + supporters)
    - Two-part scoring for party members and supporters

11. `closed_2` - Альтернативное мнение в органе (4 pts)
    - Alternative opinion in representative body
    - Scoring: 100% achievement = 4 pts, 94% = 2 pts, <94% = 0 pts

12. `closed_3` - Целевые показатели АГП (уровень) (5 pts)
    - AGP target indicators (level)
    - Scoring: 105-110% = 5 pts, Achieved = 3 pts, Not achieved = 0 pts

13. `closed_4` - Целевые показатели АГП (качество) (5 pts)
    - AGP target indicators (quality)
    - Scoring: 105-110% = 5 pts, Achieved = 3 pts, Not achieved = 0 pts

14. `closed_5` - Экономическая привлекательность МО (3 pts)
    - Economic attractiveness of municipality
    - Scoring: Low = 3 pts, Medium = 2 pts, High = 1 pt

**Block 2: Care & Attention** - 9 points
15. `closed_6` - Работа с ветеранами СВО (закрытый) (3 pts)
    - SVO veterans work (closed rating)

16. `closed_7` - Политическая деятельность ветеранов (6 pts)
    - Political activity of veterans (party members + supporters)

**Block 3: Development** - 3 points
17. `closed_8` - Проект Гордость Липецкой земли (2 pts)
    - Project "Pride of Lipetsk Land"
    - Scoring: ≥1 representative = 2 pts, None = 0 pts

**CLOSED TOTAL: 8 criteria = 35 points**

---

### Penalty System (Штрафные критерии)

Three penalty criteria that **reduce the total score**:

18. `pen_1` - Конфликты с региональной властью (-3 to -2 pts)
    - Public conflict with Governor/Government = -3
    - Conflict with deputy/minister = -2

19. `pen_2` - Внутримуниципальные конфликты (-3 to -1 pts)
    - Systematic conflicts (≥4/year) = -3
    - One significant public conflict = -2
    - Episodic conflicts (≤3/year) = -1

20. `pen_3` - Правоохранительные органы (-5 to -2 pts)
    - Criminal case against officials = -5
    - Checks/arrests of lower-ranking officials = -2

**PENALTIES: Up to -10 points total reduction**

---

### Risk Zones & Assessment

Final score determines stability zone:

| Zone | Score Range | Status | Assessment |
|------|-------------|--------|------------|
| **Зелёная** (Green) | 53-66 | High Stability | Resignation unlikely, significant resources for management & career growth |
| **Жёлтая** (Yellow) | 29-52 | Conditional Stability | Risks exist, requires correction of management/political strategy |
| **Красная** (Red) | 0-28 | Low Stability | High risk of resignation in medium-term, serious systemic problems |

---

## Technical Implementation

###  Database Schema Changes

#### New Columns Added to `dim_indicator`

```sql
ALTER TABLE dim_indicator ADD COLUMN rating_type VARCHAR(50);
-- Values: 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ' (or NULL for penalties)

ALTER TABLE dim_indicator ADD COLUMN is_penalty BOOLEAN DEFAULT FALSE;
-- TRUE for penalty criteria

ALTER TABLE dim_indicator ADD COLUMN max_points INTEGER;
-- Maximum points for this criterion (3-6 for normal, negative for penalties)
```

#### Indicator Codes

All indicators now use standardized codes:
- **PUBLIC**: `pub_1` through `pub_9`
- **CLOSED**: `closed_1` through `closed_8`
- **PENALTIES**: `pen_1` through `pen_3`

---

### Migration Execution

The migration `implement_official_methodology()` in `backend/migrations.py`:

1. **Adds necessary columns** to `dim_indicator` table if they don't exist
2. **Creates 16 official criteria** with proper codes, names, blocks, and point scales
3. **Sets up penalty system** with negative point values
4. **Idempotent design** - can be run multiple times without causing errors

**Execution point**: Automatically runs on application startup via `run_all_migrations()`

**Order of execution** (in `run_all_migrations`):
1. `apply_dim_indicator_columns_migration()` - Fix table structure
2. `apply_leader_name_column_migration()` - Add leader names
3. `apply_criteria_blocks_migration()` - Create criteria blocks
4. `ensure_proper_indicator_codes()` - Ensure proper codes
5. `fix_fact_indicator_scores()` - Fix NULL scores
6. **`implement_official_methodology()`** - Apply official methodology

---

### API Changes Required

#### New Endpoint: Calculate Official Methodology Score

```
POST /api/rating/calculate-methodology-score
```

**Request:**
```json
{
  "mo_id": 1,
  "period_id": 1,
  "rating_type": "ПУБЛИЧНЫЙ" // or "ЗАКРЫТЫЙ"
}
```

**Response:**
```json
{
  "mo_id": 1,
  "mo_name": "Липецк",
  "rating_type": "ПУБЛИЧНЫЙ",
  "period": "2024-01",
  "scores": {
    "political_management": 14,
    "care_attention": 9,
    "development": 8,
    "subtotal": 31,
    "penalties": -2,
    "total": 29
  },
  "risk_zone": "Жёлтая",
  "description": "Conditional stability"
}
```

#### Updated Rating Endpoint

```
GET /api/rating/comprehensive
```

Should return:
- PUBLIC rating (ПУБЛИЧНЫЙ): 31 points max
- CLOSED rating (ЗАКРЫТЫЙ): 35 points max
- Risk zone classification
- Penalty breakdown

---

### Frontend Changes Required

#### Rating Page (`frontend/src/pages/RatingPage.jsx`)

1. **Two-tier display**:
   - PUBLIC rating section (9 criteria, 31 points)
   - CLOSED rating section (8 criteria, 35 points)
   - Penalty section (3 criteria, -10 points max)

2. **Risk zone visualization**:
   - Green (53-66): Checkmark icon, green background
   - Yellow (29-52): Warning icon, yellow background
   - Red (0-28): X icon, red background

3. **Score breakdown**:
   - By block (Political Management, Care & Attention, Development)
   - By rating type
   - Penalty impact visualization

4. **Updated blocksConfig** should reflect new structure:
```javascript
const blocksConfig = [
  {
    id: 1,
    name: 'ПУБЛИЧНЫЙ РЕЙТИНГ',
    color: 'blue',
    maxPoints: 31,
    criteria: [
      { code: 'pub_1', number: '1', label: 'Поддержка руководства области', max: 3 },
      { code: 'pub_2', number: '2', label: 'Выполнение задач АГП', max: 5 },
      // ... more PUBLIC criteria
    ]
  },
  {
    id: 2,
    name: 'ЗАКРЫТЫЙ РЕЙТИНГ',
    color: 'purple',
    maxPoints: 35,
    criteria: [
      { code: 'closed_1', number: '1', label: 'Партийное мнение в администрации', max: 6 },
      // ... more CLOSED criteria
    ]
  },
  {
    id: 3,
    name: 'ШТРАФНЫЕ КРИТЕРИИ',
    color: 'red',
    isPenalty: true,
    criteria: [
      { code: 'pen_1', number: '1', label: 'Конфликты с региональной властью', max: -3 },
      // ... more PENALTY criteria
    ]
  }
];
```

---

## Migration Status

### Completed
- [x] Database migration function created and integrated
- [x] SQL migration file created for manual execution if needed
- [x] Documentation created

### In Progress
- [ ] SQLAlchemy models updated with new columns
- [ ] API endpoints created for methodology calculations
- [ ] Frontend updated to display official methodology

### Pending
- [ ] Testing with sample data
- [ ] GitHub commit and push

---

## Data Backward Compatibility

**Important Considerations:**

1. **Existing data in `fact_indicator` table**:
   - Old criteria codes (pm_01, ca_01, dev_01, pen_01) will need mapping or cleanup
   - Old uniform 0-10 scale values may need to be converted to variable point scales

2. **Migration Strategy**:
   - Option A: Keep old data, create separate rating calculation function
   - Option B: Migrate old scores to new criteria (complex mapping)
   - Option C: Start fresh with official methodology (data loss)

3. **Recommended Approach**:
   - Keep old data intact for audit trail
   - Use new criteria codes (pub_*, closed_*, pen_*) going forward
   - Separate API endpoints for old vs new methodology
   - Eventually deprecate old system

---

## Testing Checklist

- [ ] Database migration runs without errors
- [ ] All 16 official criteria are created with correct codes
- [ ] Column values are set correctly (rating_type, max_points, is_penalty)
- [ ] Penalty criteria have negative max_points values
- [ ] API correctly calculates PUBLIC rating (0-31 pts)
- [ ] API correctly calculates CLOSED rating (0-35 pts)
- [ ] API correctly applies penalties (-3 to -10 pts)
- [ ] Risk zones are correctly assigned based on final score
- [ ] Frontend displays two-tier rating system
- [ ] Penalty visualization works correctly
- [ ] Sample data calculation matches manual methodology
- [ ] All 20 municipalities display correct scores

---

## References

1. **Methodology Document**: "Методика оценки эффективности деятельности глав администраций МО 23.10.pdf"
2. **Slides analyzed**: 4, 5, 7-15, 17-24, 25-28
3. **Database**: PostgreSQL with SQLAlchemy ORM
4. **Frontend**: React with custom scoring components
5. **Backend**: FastAPI with Python

---

## Contact & Support

For questions about the official methodology implementation, refer to:
- Source methodology PDF
- This documentation file
- Database migration code in `backend/migrations.py`
- API implementation in `backend/routes/`

---

**Status**: Active Implementation Phase
**Next Steps**: Update frontend and create API endpoints
