"""
Rating routes v2 - Hierarchical structure with criteria blocks
Returns data organized as: Block → Criteria → Indicators
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import Optional, List, Dict
from datetime import datetime
import logging

from database import get_db
from models import DimMO, FactSummary, DimPeriod, DimIndicator, DimCriteriaBlock, DimPenalty, FactIndicator, FactPenalty

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
    Get rating table with hierarchical structure:
    Block → Criteria → Indicator values
    """
    try:
        # Check if leader_name column exists
        has_leader_name = False
        try:
            db.execute(text("SELECT leader_name FROM dim_mo LIMIT 1"))
            has_leader_name = True
        except Exception as e:
            db.rollback()
            has_leader_name = False
            logger.warning(f"leader_name column does not exist: {str(e)}")

        # Build base query
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

        # Filter by period
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

        # Filter by version
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

        # Determine period_id for fetching indicators
        period_id = None
        if period:
            period_date = datetime.strptime(period, "%Y-%m").date()
            period_obj = db.query(DimPeriod).filter(
                and_(
                    DimPeriod.date_from <= period_date,
                    DimPeriod.date_to >= period_date,
                )
            ).first()
            if period_obj:
                period_id = period_obj.period_id

        # Format response with hierarchical block structure
        items = []
        for r in results:
            mo_id = r[0]

            # Fetch criteria blocks with their indicators for this MO
            blocks = get_criteria_blocks_for_mo(db, mo_id, period_id, version)

            # Fetch penalties for this MO
            penalties = get_penalties_for_mo(db, mo_id, period_id, version)

            item = {
                "mo_id": mo_id,
                "mo_name": r[1],
                "leader_name": r[2] or "Не указано",
                "score_public": float(r[3]) if r[3] else 0,
                "score_closed": float(r[4]) if r[4] else 0,
                "score_penalties": float(r[5]) if r[5] else 0,
                "score_total": float(r[6]) if r[6] else 0,
                "zone": r[7],
                "updated_at": r[8].isoformat() if r[8] else None,
                "blocks": blocks,  # Hierarchical block structure
                "penalties": penalties,  # Penalty information
            }
            items.append(item)

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


def get_criteria_blocks_for_mo(db: Session, mo_id: int, period_id: Optional[int], version_id: Optional[int]) -> List[Dict]:
    """
    Fetch criteria organized by blocks for a specific MO
    Returns: List of blocks, each containing list of criteria with their values
    """
    try:
        # Get all criteria blocks
        blocks = db.query(DimCriteriaBlock).order_by(DimCriteriaBlock.block_order).all()

        result = []
        for block in blocks:
            # Get indicators for this block
            indicators = db.query(DimIndicator).filter(
                DimIndicator.block_id == block.block_id
            ).order_by(DimIndicator.weight.desc()).all()

            criteria_list = []
            block_score = 0

            for indicator in indicators:
                # Get fact value for this indicator
                fact_query = db.query(FactIndicator).filter(
                    FactIndicator.mo_id == mo_id,
                    FactIndicator.ind_id == indicator.ind_id
                )

                if period_id:
                    fact_query = fact_query.filter(FactIndicator.period_id == period_id)
                if version_id:
                    fact_query = fact_query.filter(FactIndicator.version_id == version_id)

                fact = fact_query.first()

                score = float(fact.score) if fact and fact.score else 0
                block_score += score

                criteria_list.append({
                    "code": indicator.code,
                    "name": indicator.name,
                    "description": indicator.description,
                    "is_public": indicator.is_public,
                    "score": score,
                    "value_raw": float(fact.value_raw) if fact and fact.value_raw else None,
                    "value_norm": float(fact.value_norm) if fact and fact.value_norm else None,
                    "target": float(fact.target) if fact and fact.target else None,
                })

            result.append({
                "block_id": block.block_id,
                "block_name": block.block_name,
                "block_order": block.block_order,
                "description": block.description,
                "score": block_score,
                "criteria_count": len(criteria_list),
                "criteria": criteria_list,
            })

        return result
    except Exception as e:
        logger.warning(f"Error fetching criteria blocks: {str(e)}")
        return []


def get_penalties_for_mo(db: Session, mo_id: int, period_id: Optional[int], version_id: Optional[int]) -> List[Dict]:
    """
    Fetch penalties for a specific MO
    Returns: List of penalties with their details
    """
    try:
        penalty_query = db.query(FactPenalty).filter(
            FactPenalty.mo_id == mo_id
        )

        if period_id:
            penalty_query = penalty_query.filter(FactPenalty.period_id == period_id)
        if version_id:
            penalty_query = penalty_query.filter(FactPenalty.version_id == version_id)

        facts = penalty_query.all()

        result = []
        for fact in facts:
            penalty = db.query(DimPenalty).filter(
                DimPenalty.pen_id == fact.pen_id
            ).first()

            if penalty:
                result.append({
                    "code": penalty.code,
                    "name": penalty.name,
                    "description": penalty.description,
                    "block": penalty.block,
                    "score": float(fact.score_negative) if fact.score_negative else 0,
                    "details": fact.details,
                })

        return result
    except Exception as e:
        logger.warning(f"Error fetching penalties: {str(e)}")
        return []
