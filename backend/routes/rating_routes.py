from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
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
    """
    try:
        query = db.query(
            DimMO.mo_id,
            DimMO.mo_name,
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
        items = [
            {
                "mo_id": r[0],
                "mo_name": r[1],
                "score_public": float(r[2]) if r[2] else 0,
                "score_closed": float(r[3]) if r[3] else 0,
                "score_penalties": float(r[4]) if r[4] else 0,
                "score_total": float(r[5]) if r[5] else 0,
                "zone": r[6],
                "updated_at": r[7].isoformat() if r[7] else None,
            }
            for r in results
        ]

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
        logger.error(f"Error fetching rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching rating")


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

        query = db.query(
            DimMO.mo_id,
            DimMO.mo_name,
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
            period_date = datetime.strptime(period, "%Y-%m").date()
            period_obj = db.query(DimPeriod).filter(
                and_(
                    DimPeriod.date_from <= period_date,
                    DimPeriod.date_to >= period_date,
                )
            ).first()
            if period_obj:
                query = query.filter(FactSummary.period_id == period_obj.period_id)

        results = query.all()

        items = [
            {
                "mo_id": r[0],
                "mo_name": r[1],
                "score_public": float(r[2]) if r[2] else 0,
                "score_closed": float(r[3]) if r[3] else 0,
                "score_total": float(r[4]) if r[4] else 0,
                "zone": r[5],
            }
            for r in results
        ]

        return {
            "status": "success",
            "count": len(items),
            "data": items,
        }

    except Exception as e:
        logger.error(f"Error comparing MOs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error comparing MOs")
