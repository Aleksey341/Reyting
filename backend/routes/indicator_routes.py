from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models import DimIndicator, FactIndicator, DimMO, DimPeriod

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def get_indicators(
    block: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Get list of indicators with filters"""
    try:
        query = db.query(DimIndicator)

        if block:
            query = query.filter(DimIndicator.block == block)

        if is_public is not None:
            query = query.filter(DimIndicator.is_public == is_public)

        indicators = query.all()

        return {
            "status": "success",
            "count": len(indicators),
            "data": [
                {
                    "ind_id": ind.ind_id,
                    "code": ind.code,
                    "name": ind.name,
                    "block": ind.block,
                    "unit": ind.unit,
                    "is_public": ind.is_public,
                    "owner_org": ind.owner_org,
                }
                for ind in indicators
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching indicators: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching indicators")


@router.get("/{mo_id}")
async def get_mo_indicators(
    mo_id: int,
    period_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all indicators for a specific MO"""
    try:
        query = db.query(
            DimIndicator.ind_id,
            DimIndicator.code,
            DimIndicator.name,
            DimIndicator.block,
            FactIndicator.value_raw,
            FactIndicator.score,
            FactIndicator.target,
        ).join(
            FactIndicator,
            DimIndicator.ind_id == FactIndicator.ind_id
        ).filter(
            FactIndicator.mo_id == mo_id
        )

        if period_id:
            query = query.filter(FactIndicator.period_id == period_id)

        results = query.all()

        return {
            "status": "success",
            "mo_id": mo_id,
            "count": len(results),
            "data": [
                {
                    "ind_id": r[0],
                    "code": r[1],
                    "name": r[2],
                    "block": r[3],
                    "value_raw": float(r[4]) if r[4] else None,
                    "score": float(r[5]) if r[5] else None,
                    "target": float(r[6]) if r[6] else None,
                }
                for r in results
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching MO indicators: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching indicators")
