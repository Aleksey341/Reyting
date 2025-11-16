"""
Rating routes - Get ratings for municipalities.
Handles both cases: with and without leader_name field.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import Optional
from datetime import datetime
import logging

from database import get_db
from models import DimMO, FactSummary, DimPeriod

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def get_rating(
    period: Optional[str] = Query(None),
    version: Optional[int] = Query(None),
    sort: str = Query("score_total", description="Field to sort by"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get rating table with MO scores.
    Supports sorting, pagination, and filtering by period/version.
    Works with or without leader_name field.
    """
    try:
        # Check if leader_name column exists
        has_leader_name = False
        try:
            # Try to query with leader_name
            db.execute(
                text("SELECT leader_name FROM dim_mo LIMIT 1")
            )
            has_leader_name = True
        except Exception:
            has_leader_name = False
            logger.warning("leader_name column does not exist, proceeding without it")

        # Build query based on column availability
        if has_leader_name:
            query = db.query(
                DimMO.mo_id,
                DimMO.mo_name,
                DimMO.leader_name,
                FactSummary.score_public,
                FactSummary.score_closed,
                FactSummary.score_penalties,
                FactSummary.score_total,
                FactSummary.zone,
                FactSummary.updated_at,
            ).join(
                FactSummary,
                and_(DimMO.mo_id == FactSummary.mo_id)
            )
        else:
            query = db.query(
                DimMO.mo_id,
                DimMO.mo_name,
                text("NULL as leader_name"),
                FactSummary.score_public,
                FactSummary.score_closed,
                FactSummary.score_penalties,
                FactSummary.score_total,
                FactSummary.zone,
                FactSummary.updated_at,
            ).join(
                FactSummary,
                and_(DimMO.mo_id == FactSummary.mo_id)
            )

        if period:
            try:
                period_date = datetime.strptime(period, "%Y-%m").date()
                period_obj = db.query(DimPeriod).filter(
                    and_(
                        DimPeriod.date_from <= period_date,
                        DimPeriod.date_to >= period_date,
                    )
                ).first()
                if period_obj:
                    query = query.filter(FactSummary.period_id == period_obj.period_id)
                else:
                    logger.warning(f"Period not found for date: {period_date}")
                    return {
                        "status": "success",
                        "total": 0,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": 0,
                        "data": [],
                    }
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid period format")

        if version:
            query = query.filter(FactSummary.version_id == version)

        # Apply sorting
        if sort == "score_total":
            sort_col = FactSummary.score_total
        elif sort == "score_public":
            sort_col = FactSummary.score_public
        elif sort == "mo_name":
            sort_col = DimMO.mo_name
        else:
            sort_col = FactSummary.score_total

        if order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Count total
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        # Format response
        items = []
        for r in results:
            items.append({
                "mo_id": r[0],
                "mo_name": r[1],
                "leader_name": r[2] or "Не указано",
                "score_public": float(r[3]) if r[3] else 0,
                "score_closed": float(r[4]) if r[4] else 0,
                "score_penalties": float(r[5]) if r[5] else 0,
                "score_total": float(r[6]) if r[6] else 0,
                "zone": r[7],
                "indicators": {},
                "penalties": {},
                "updated_at": r[8].isoformat() if r[8] else None,
            })

        return {
            "status": "success",
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": items,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching rating: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching rating: {str(e)}")


@router.get("/comparison")
async def compare_mos(
    mo_ids: str = Query(..., description="Comma-separated MO IDs"),
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Compare multiple MOs side-by-side.
    """
    try:
        mo_id_list = [int(x.strip()) for x in mo_ids.split(",")]

        # Check if leader_name exists
        has_leader_name = False
        try:
            db.execute(text("SELECT leader_name FROM dim_mo LIMIT 1"))
            has_leader_name = True
        except Exception:
            has_leader_name = False

        if has_leader_name:
            query = db.query(
                DimMO.mo_id,
                DimMO.mo_name,
                DimMO.leader_name,
                FactSummary.score_public,
                FactSummary.score_closed,
                FactSummary.score_total,
                FactSummary.zone,
            ).join(
                FactSummary,
                DimMO.mo_id == FactSummary.mo_id
            ).filter(
                DimMO.mo_id.in_(mo_id_list)
            )
        else:
            query = db.query(
                DimMO.mo_id,
                DimMO.mo_name,
                text("NULL as leader_name"),
                FactSummary.score_public,
                FactSummary.score_closed,
                FactSummary.score_total,
                FactSummary.zone,
            ).join(
                FactSummary,
                DimMO.mo_id == FactSummary.mo_id
            ).filter(
                DimMO.mo_id.in_(mo_id_list)
            )

        if period:
            try:
                period_date = datetime.strptime(period, "%Y-%m").date()
                period_obj = db.query(DimPeriod).filter(
                    and_(
                        DimPeriod.date_from <= period_date,
                        DimPeriod.date_to >= period_date,
                    )
                ).first()
                if period_obj:
                    query = query.filter(FactSummary.period_id == period_obj.period_id)
            except ValueError:
                pass

        results = query.all()

        items = [
            {
                "mo_id": r[0],
                "mo_name": r[1],
                "leader_name": r[2] or "Не указано",
                "score_public": float(r[3]) if r[3] else 0,
                "score_closed": float(r[4]) if r[4] else 0,
                "score_total": float(r[5]) if r[5] else 0,
                "zone": r[6],
            }
            for r in results
        ]

        return {
            "status": "success",
            "count": len(items),
            "data": items,
        }

    except Exception as e:
        logger.error(f"Error comparing MOs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error comparing MOs: {str(e)}")
