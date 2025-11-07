"""
API routes for data cleanup operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from database import get_db
from models import DimMO, DimPeriod, DimIndicator, DimMethodology, FactIndicator, FactSummary

router = APIRouter()
logger = logging.getLogger(__name__)


@router.delete("/clear-all-data")
async def clear_all_data(
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    ⚠️ DANGER: Clear ALL data from database (keeps structure and municipalities).

    This will delete:
    - All indicator values (fact_indicator)
    - All calculated scores (fact_summary)
    - All periods (dim_period)
    - All indicators (dim_indicator)
    - All methodologies (dim_methodology)

    This will KEEP:
    - Municipality definitions (dim_mo) with boundaries
    - Database structure (tables)

    Requires confirm=True parameter for safety.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=True to delete all data. This is a destructive operation!"
        )

    try:
        # Count before deletion
        fact_indicator_count = db.query(FactIndicator).count()
        fact_summary_count = db.query(FactSummary).count()
        periods_count = db.query(DimPeriod).count()
        indicators_count = db.query(DimIndicator).count()
        methodologies_count = db.query(DimMethodology).count()

        logger.warning(f"Starting full data deletion. Current counts:")
        logger.warning(f"  - fact_indicator: {fact_indicator_count}")
        logger.warning(f"  - fact_summary: {fact_summary_count}")
        logger.warning(f"  - dim_period: {periods_count}")
        logger.warning(f"  - dim_indicator: {indicators_count}")
        logger.warning(f"  - dim_methodology: {methodologies_count}")

        # Delete in correct order (respect foreign keys)
        db.query(FactSummary).delete()
        db.query(FactIndicator).delete()
        db.query(DimPeriod).delete()
        db.query(DimIndicator).delete()
        db.query(DimMethodology).delete()

        db.commit()

        logger.warning("All data deleted successfully")

        return {
            "status": "success",
            "message": "All data deleted successfully",
            "deleted": {
                "fact_indicator": fact_indicator_count,
                "fact_summary": fact_summary_count,
                "dim_period": periods_count,
                "dim_indicator": indicators_count,
                "dim_methodology": methodologies_count
            },
            "preserved": {
                "dim_mo": db.query(DimMO).count(),
                "note": "Municipalities and boundaries preserved"
            }
        }

    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting data: {str(e)}")


@router.delete("/clear-period-data")
async def clear_period_data(
    period_id: int = Query(..., description="Period ID to delete"),
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    Delete all data for a specific period.

    This will delete:
    - All indicator values for this period (fact_indicator)
    - All calculated scores for this period (fact_summary)
    - The period itself (dim_period)

    Requires confirm=True parameter for safety.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=True to delete period data"
        )

    try:
        # Check if period exists
        period = db.query(DimPeriod).filter(DimPeriod.period_id == period_id).first()
        if not period:
            raise HTTPException(status_code=404, detail=f"Period {period_id} not found")

        # Count before deletion
        fact_indicator_count = db.query(FactIndicator).filter(
            FactIndicator.period_id == period_id
        ).count()
        fact_summary_count = db.query(FactSummary).filter(
            FactSummary.period_id == period_id
        ).count()

        logger.info(f"Deleting data for period {period_id} ({period.date_from} - {period.date_to})")
        logger.info(f"  - fact_indicator: {fact_indicator_count}")
        logger.info(f"  - fact_summary: {fact_summary_count}")

        # Delete data
        db.query(FactSummary).filter(FactSummary.period_id == period_id).delete()
        db.query(FactIndicator).filter(FactIndicator.period_id == period_id).delete()
        db.query(DimPeriod).filter(DimPeriod.period_id == period_id).delete()

        db.commit()

        logger.info(f"Period {period_id} data deleted successfully")

        return {
            "status": "success",
            "message": f"Period {period_id} data deleted successfully",
            "deleted": {
                "period": f"{period.date_from} - {period.date_to}",
                "fact_indicator": fact_indicator_count,
                "fact_summary": fact_summary_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting period data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting period data: {str(e)}")


@router.delete("/clear-fact-data")
async def clear_fact_data(
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    Clear only fact tables (indicator values and scores).

    This will delete:
    - All indicator values (fact_indicator)
    - All calculated scores (fact_summary)

    This will KEEP:
    - Municipalities (dim_mo)
    - Periods (dim_period)
    - Indicators (dim_indicator)
    - Methodologies (dim_methodology)

    Useful when you want to reload data but keep the structure.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=True to delete fact data"
        )

    try:
        fact_indicator_count = db.query(FactIndicator).count()
        fact_summary_count = db.query(FactSummary).count()

        logger.info(f"Clearing fact tables:")
        logger.info(f"  - fact_indicator: {fact_indicator_count}")
        logger.info(f"  - fact_summary: {fact_summary_count}")

        db.query(FactSummary).delete()
        db.query(FactIndicator).delete()

        db.commit()

        logger.info("Fact data cleared successfully")

        return {
            "status": "success",
            "message": "Fact data cleared successfully",
            "deleted": {
                "fact_indicator": fact_indicator_count,
                "fact_summary": fact_summary_count
            },
            "preserved": {
                "dim_mo": db.query(DimMO).count(),
                "dim_period": db.query(DimPeriod).count(),
                "dim_indicator": db.query(DimIndicator).count(),
                "dim_methodology": db.query(DimMethodology).count()
            }
        }

    except Exception as e:
        logger.error(f"Error clearing fact data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing fact data: {str(e)}")


@router.get("/data-stats")
async def get_data_stats(db: Session = Depends(get_db)):
    """
    Get current data statistics for all tables.
    Useful before deciding what to delete.
    """
    try:
        # Get all periods with details
        periods = db.query(DimPeriod).all()
        period_details = []

        for period in periods:
            indicator_count = db.query(FactIndicator).filter(
                FactIndicator.period_id == period.period_id
            ).count()
            summary_count = db.query(FactSummary).filter(
                FactSummary.period_id == period.period_id
            ).count()

            period_details.append({
                "period_id": period.period_id,
                "date_from": period.date_from,
                "date_to": period.date_to,
                "period_type": period.period_type,
                "indicator_values": indicator_count,
                "summaries": summary_count
            })

        stats = {
            "municipalities": db.query(DimMO).count(),
            "indicators": db.query(DimIndicator).count(),
            "periods": db.query(DimPeriod).count(),
            "methodologies": db.query(DimMethodology).count(),
            "indicator_values_total": db.query(FactIndicator).count(),
            "summaries_total": db.query(FactSummary).count(),
            "period_details": period_details
        }

        return {
            "status": "success",
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
