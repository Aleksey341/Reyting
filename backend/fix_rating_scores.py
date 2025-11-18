#!/usr/bin/env python3
"""
Fix zero rating scores by ensuring indicators have proper rating_type
and recalculating aggregated scores
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://reyting_user:password@localhost:5432/reytingdb')

try:
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    logger.info("=" * 80)
    logger.info("FIX: Rating Scores - Ensure rating_type and recalculate aggregates")
    logger.info("=" * 80)

    # STEP 1: Ensure all pub_*, closed_*, pen_* indicators have rating_type set
    logger.info("\n[STEP 1] Setting rating_type on indicators...")

    updates = [
        ("UPDATE dim_indicator SET rating_type = 'ПУБЛИЧНЫЙ' WHERE code LIKE 'pub_%' AND rating_type IS NULL",
         "PUBLIC indicators (pub_*)"),
        ("UPDATE dim_indicator SET rating_type = 'ЗАКРЫТЫЙ' WHERE code LIKE 'closed_%' AND rating_type IS NULL",
         "CLOSED indicators (closed_*)"),
        ("UPDATE dim_indicator SET is_penalty = TRUE WHERE code LIKE 'pen_%' AND is_penalty = FALSE",
         "PENALTY indicators (pen_*)")
    ]

    for sql, desc in updates:
        result = session.execute(text(sql))
        session.commit()
        logger.info(f"  ✓ Updated {desc}")

    # STEP 2: Check current state
    logger.info("\n[STEP 2] Checking current indicator state...")
    result = session.execute(text("""
        SELECT
            rating_type,
            COUNT(*) as cnt
        FROM dim_indicator
        GROUP BY rating_type
        ORDER BY rating_type
    """))
    for row in result:
        logger.info(f"  - rating_type='{row[0]}': {row[1]} indicators")

    # STEP 3: Check FactIndicator scores
    logger.info("\n[STEP 3] Checking FactIndicator scores...")
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN score > 0 THEN 1 END) as positive,
            COUNT(CASE WHEN score = 0 THEN 1 END) as zero,
            COUNT(CASE WHEN score < 0 THEN 1 END) as negative,
            ROUND(AVG(score)::numeric, 2) as avg_score
        FROM fact_indicator
    """))
    row = result.first()
    logger.info(f"  - Total FactIndicator records: {row[0]}")
    logger.info(f"    - Positive scores (>0): {row[1]}")
    logger.info(f"    - Zero scores (=0): {row[2]}")
    logger.info(f"    - Negative scores (<0): {row[3]}")
    logger.info(f"    - Average score: {row[4]}")

    # STEP 4: Manual test aggregation for latest period
    logger.info("\n[STEP 4] Testing aggregation for latest period...")
    result = session.execute(text("SELECT MAX(period_id) FROM dim_period"))
    latest_period = result.scalar()
    logger.info(f"  Latest period_id: {latest_period}")

    if latest_period:
        # PUBLIC
        result = session.execute(text("""
            SELECT SUM(fi.score) as total, COUNT(*) as cnt
            FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.period_id = :period_id AND di.rating_type = 'ПУБЛИЧНЫЙ'
        """), {"period_id": latest_period})
        row = result.first()
        logger.info(f"  - PUBLIC (rating_type='ПУБЛИЧНЫЙ'): SUM={row[0]}, COUNT={row[1]}")

        # CLOSED
        result = session.execute(text("""
            SELECT SUM(fi.score) as total, COUNT(*) as cnt
            FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.period_id = :period_id AND di.rating_type = 'ЗАКРЫТЫЙ'
        """), {"period_id": latest_period})
        row = result.first()
        logger.info(f"  - CLOSED (rating_type='ЗАКРЫТЫЙ'): SUM={row[0]}, COUNT={row[1]}")

        # PENALTIES
        result = session.execute(text("""
            SELECT SUM(fi.score) as total, COUNT(*) as cnt
            FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.period_id = :period_id AND di.is_penalty = TRUE
        """), {"period_id": latest_period})
        row = result.first()
        logger.info(f"  - PENALTIES (is_penalty=true): SUM={row[0]}, COUNT={row[1]}")

    # STEP 5: Recalculate FactSummary aggregates
    logger.info("\n[STEP 5] Recalculating FactSummary aggregates...")

    # Delete existing FactSummary to start fresh
    session.execute(text("DELETE FROM fact_summary"))
    session.commit()
    logger.info("  ✓ Cleared existing FactSummary records")

    # Get all MO-Period combinations with data
    result = session.execute(text("""
        SELECT DISTINCT mo_id, period_id
        FROM fact_indicator
        WHERE score IS NOT NULL
        ORDER BY period_id DESC, mo_id
    """))
    combinations = result.fetchall()
    logger.info(f"  Found {len(combinations)} MO-Period combinations to aggregate")

    # Recalculate scores for each combination
    inserted = 0
    for mo_id, period_id in combinations:
        # PUBLIC
        result = session.execute(text("""
            SELECT SUM(fi.score) FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.mo_id = :mo_id AND fi.period_id = :period_id AND di.rating_type = 'ПУБЛИЧНЫЙ'
        """), {"mo_id": mo_id, "period_id": period_id})
        public_score = result.scalar() or 0.0

        # CLOSED
        result = session.execute(text("""
            SELECT SUM(fi.score) FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.mo_id = :mo_id AND fi.period_id = :period_id AND di.rating_type = 'ЗАКРЫТЫЙ'
        """), {"mo_id": mo_id, "period_id": period_id})
        closed_score = result.scalar() or 0.0

        # PENALTIES
        result = session.execute(text("""
            SELECT SUM(fi.score) FROM fact_indicator fi
            JOIN dim_indicator di ON fi.ind_id = di.ind_id
            WHERE fi.mo_id = :mo_id AND fi.period_id = :period_id AND di.is_penalty = TRUE
        """), {"mo_id": mo_id, "period_id": period_id})
        penalties = result.scalar() or 0.0

        # Total
        total_score = max(0.0, public_score + closed_score + penalties)

        # Zone
        if total_score >= 53:
            zone = 'Зелёная'
        elif total_score >= 29:
            zone = 'Жёлтая'
        else:
            zone = 'Красная'

        # Insert
        session.execute(text("""
            INSERT INTO fact_summary (mo_id, period_id, version_id, score_public, score_closed, score_penalties, score_total, zone, updated_at)
            VALUES (:mo_id, :period_id, 1, :score_public, :score_closed, :score_penalties, :score_total, :zone, NOW())
        """), {
            "mo_id": mo_id,
            "period_id": period_id,
            "score_public": public_score,
            "score_closed": closed_score,
            "score_penalties": penalties,
            "score_total": total_score,
            "zone": zone
        })
        inserted += 1

    session.commit()
    logger.info(f"  ✓ Recalculated and inserted {inserted} FactSummary records")

    # STEP 6: Verify results
    logger.info("\n[STEP 6] Verification - Sample of new FactSummary records...")
    result = session.execute(text("""
        SELECT mo_id, period_id, score_public, score_closed, score_penalties, score_total, zone
        FROM fact_summary
        ORDER BY period_id DESC, mo_id
        LIMIT 10
    """))
    for row in result:
        logger.info(f"  MO={row[0]:2}, Period={row[1]}: pub={row[2]:6.1f}, closed={row[3]:6.1f}, pen={row[4]:6.1f}, total={row[5]:6.1f}, zone={row[6]}")

    logger.info("\n" + "=" * 80)
    logger.info("✓ FIX COMPLETE - Scores should now display correctly")
    logger.info("=" * 80)

    session.close()

except Exception as e:
    logger.error(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
