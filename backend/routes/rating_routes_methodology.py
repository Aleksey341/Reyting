"""
Official Methodology Rating Routes
Implements the official methodology for rating municipal heads:
- PUBLIC RATING (ПУБЛИЧНЫЙ): 9 criteria, 31 points max
- CLOSED RATING (ЗАКРЫТЫЙ): 8 criteria, 35 points max
- PENALTY SYSTEM: 3 criteria that reduce total score (-3 to -5 points)
- RISK ZONES: Green (53-66), Yellow (29-52), Red (0-28)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel

from database import get_db
from models import DimMO, DimPeriod, DimIndicator, FactIndicator, FactPenalty

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for API Responses
# ============================================================================

class CriterionScore(BaseModel):
    """Individual criterion score"""
    code: str
    name: str
    block: str
    rating_type: Optional[str]  # ПУБЛИЧНЫЙ, ЗАКРЫТЫЙ, or None (penalties)
    is_penalty: bool
    max_points: int
    score: float
    percentage: float  # score/max_points * 100

    class Config:
        from_attributes = True


class BlockScore(BaseModel):
    """Block (category) score with criteria breakdown"""
    block_name: str
    rating_type: Optional[str]
    max_points: int
    score: float
    percentage: float
    criteria_count: int
    criteria: List[CriterionScore]


class RiskZone(BaseModel):
    """Risk zone information"""
    zone_name: str
    score_range: str
    status: str
    assessment: str


class MethodologyScore(BaseModel):
    """Complete official methodology score for a municipality"""
    mo_id: int
    mo_name: str
    leader_name: Optional[str]
    rating_type: str  # ПУБЛИЧНЫЙ or ЗАКРЫТЫЙ
    period_id: int
    period_date: str

    # Score breakdown by rating type
    public_score: Optional[float] = None
    closed_score: Optional[float] = None
    penalties: float = 0.0

    # Score summaries
    subtotal: float  # public or closed (before penalties)
    total_score: float  # after penalties

    # Risk zone
    risk_zone: str  # Зелёная, Жёлтая, Красная
    risk_status: str  # High Stability, Conditional Stability, Low Stability

    # Block breakdown
    blocks: List[BlockScore]

    class Config:
        from_attributes = True


class ComprehensiveRating(BaseModel):
    """Complete rating with both PUBLIC and CLOSED scores"""
    mo_id: int
    mo_name: str
    leader_name: Optional[str]
    period_id: int
    period_date: str

    public_rating: MethodologyScore
    closed_rating: MethodologyScore

    # Combined assessment
    combined_score: float  # Average of public and closed
    combined_zone: str  # Overall risk zone

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

def get_risk_zone(score: float) -> tuple[str, str]:
    """
    Determine risk zone based on score.
    Returns (zone_name, status) tuple.
    """
    if score >= 53:
        return ("Зелёная", "High Stability")
    elif score >= 29:
        return ("Жёлтая", "Conditional Stability")
    else:
        return ("Красная", "Low Stability")


def calculate_methodology_score(
    db: Session,
    mo_id: int,
    period_id: int,
    rating_type: str
) -> Optional[MethodologyScore]:
    """
    Calculate official methodology score for a municipality.

    Args:
        db: Database session
        mo_id: Municipality ID
        period_id: Period ID
        rating_type: 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ'

    Returns:
        MethodologyScore object with complete breakdown, or None if data not found
    """
    try:
        # Get municipality
        mo = db.query(DimMO).filter(DimMO.mo_id == mo_id).first()
        if not mo:
            return None

        # Get period
        period = db.query(DimPeriod).filter(DimPeriod.period_id == period_id).first()
        if not period:
            return None

        # Get all indicators for this rating type
        indicators = db.query(DimIndicator).filter(
            DimIndicator.rating_type == rating_type,
            DimIndicator.is_penalty == False
        ).all()

        if not indicators:
            logger.warning(f"No indicators found for rating_type={rating_type}")
            return None

        # Get indicator codes
        indicator_codes = [ind.code for ind in indicators]

        # Get scores from fact_indicator
        fact_scores = db.query(FactIndicator).filter(
            FactIndicator.mo_id == mo_id,
            FactIndicator.period_id == period_id,
            FactIndicator.ind_id.in_([ind.ind_id for ind in indicators])
        ).all()

        # Create score mapping
        score_map = {fs.indicator.code: fs.score for fs in fact_scores}

        # Build blocks and criteria
        blocks_dict: Dict[str, Dict] = {}
        total_max_points = 0
        total_score = 0.0

        criterion_scores = []

        for indicator in indicators:
            score = score_map.get(indicator.code, 0.0)
            max_pts = indicator.max_points or 0

            total_max_points += max_pts
            total_score += score

            # Create criterion score object
            criterion = CriterionScore(
                code=indicator.code,
                name=indicator.name,
                block=indicator.block or "Unknown",
                rating_type=indicator.rating_type,
                is_penalty=False,
                max_points=max_pts,
                score=score,
                percentage=(score / max_pts * 100) if max_pts > 0 else 0.0
            )
            criterion_scores.append(criterion)

            # Add to blocks dict
            block_name = indicator.block or "Unknown"
            if block_name not in blocks_dict:
                blocks_dict[block_name] = {
                    "max_points": 0,
                    "score": 0.0,
                    "criteria": [],
                    "rating_type": indicator.rating_type
                }
            blocks_dict[block_name]["max_points"] += max_pts
            blocks_dict[block_name]["score"] += score
            blocks_dict[block_name]["criteria"].append(criterion)

        # Build blocks list
        blocks = [
            BlockScore(
                block_name=block_name,
                rating_type=block_data["rating_type"],
                max_points=block_data["max_points"],
                score=block_data["score"],
                percentage=(block_data["score"] / block_data["max_points"] * 100) if block_data["max_points"] > 0 else 0.0,
                criteria_count=len(block_data["criteria"]),
                criteria=block_data["criteria"]
            )
            for block_name, block_data in blocks_dict.items()
        ]

        # Get penalties for this municipality
        penalties_value = 0.0
        penalty_indicators = db.query(DimIndicator).filter(
            DimIndicator.is_penalty == True
        ).all()

        penalty_facts = db.query(FactIndicator).filter(
            FactIndicator.mo_id == mo_id,
            FactIndicator.period_id == period_id,
            FactIndicator.ind_id.in_([ind.ind_id for ind in penalty_indicators])
        ).all()

        for fact in penalty_facts:
            penalties_value += fact.score  # scores are negative for penalties

        # Calculate total with penalties
        total_with_penalties = total_score + penalties_value

        # Determine risk zone
        zone_name, status = get_risk_zone(total_with_penalties)

        # Build response
        return MethodologyScore(
            mo_id=mo_id,
            mo_name=mo.mo_name,
            leader_name=mo.leader_name,
            rating_type=rating_type,
            period_id=period_id,
            period_date=period.date_from.isoformat() if period.date_from else "",
            public_score=total_score if rating_type == "ПУБЛИЧНЫЙ" else None,
            closed_score=total_score if rating_type == "ЗАКРЫТЫЙ" else None,
            penalties=penalties_value,
            subtotal=total_score,
            total_score=total_with_penalties,
            risk_zone=zone_name,
            risk_status=status,
            blocks=blocks
        )

    except Exception as e:
        logger.error(f"Error calculating methodology score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/methodology/score/{mo_id}")
async def get_methodology_score(
    mo_id: int,
    period_id: int = Query(..., description="Period ID"),
    rating_type: str = Query("ПУБЛИЧНЫЙ", description="ПУБЛИЧНЫЙ or ЗАКРЫТЫЙ"),
    db: Session = Depends(get_db),
):
    """
    Get official methodology score for a specific municipality and rating type.

    Parameters:
    - mo_id: Municipality ID
    - period_id: Period ID
    - rating_type: 'ПУБЛИЧНЫЙ' (PUBLIC) or 'ЗАКРЫТЫЙ' (CLOSED)

    Returns:
    - MethodologyScore with complete breakdown by blocks and criteria
    """
    if rating_type not in ["ПУБЛИЧНЫЙ", "ЗАКРЫТЫЙ"]:
        raise HTTPException(status_code=400, detail="rating_type must be 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ'")

    score = calculate_methodology_score(db, mo_id, period_id, rating_type)
    if not score:
        raise HTTPException(status_code=404, detail=f"No data found for MO {mo_id} in period {period_id}")

    return score


@router.get("/methodology/comprehensive/{mo_id}")
async def get_comprehensive_rating(
    mo_id: int,
    period_id: int = Query(..., description="Period ID"),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive rating with both PUBLIC and CLOSED scores for a municipality.

    This endpoint calculates both ПУБЛИЧНЫЙ and ЗАКРЫТЫЙ ratings and provides
    a combined assessment.

    Returns:
    - ComprehensiveRating with both public and closed ratings
    """
    # Get both ratings
    public_rating = calculate_methodology_score(db, mo_id, period_id, "ПУБЛИЧНЫЙ")
    closed_rating = calculate_methodology_score(db, mo_id, period_id, "ЗАКРЫТЫЙ")

    if not public_rating or not closed_rating:
        raise HTTPException(status_code=404, detail=f"No data found for MO {mo_id} in period {period_id}")

    # Calculate combined score (average of both)
    combined_score = (public_rating.total_score + closed_rating.total_score) / 2
    combined_zone, _ = get_risk_zone(combined_score)

    return ComprehensiveRating(
        mo_id=mo_id,
        mo_name=public_rating.mo_name,
        leader_name=public_rating.leader_name,
        period_id=period_id,
        period_date=public_rating.period_date,
        public_rating=public_rating,
        closed_rating=closed_rating,
        combined_score=combined_score,
        combined_zone=combined_zone
    )


@router.get("/methodology/all/{period_id}")
async def get_all_methodology_scores(
    period_id: int,
    rating_type: str = Query("ПУБЛИЧНЫЙ", description="ПУБЛИЧНЫЙ or ЗАКРЫТЫЙ"),
    sort: str = Query("score_total", description="Field to sort by"),
    order: str = Query("desc", description="asc or desc"),
    db: Session = Depends(get_db),
):
    """
    Get methodology scores for all municipalities in a specific period.

    Parameters:
    - period_id: Period ID
    - rating_type: 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ'
    - sort: Field to sort by (score_total, mo_name, leader_name)
    - order: Sort order (asc or desc)

    Returns:
    - List of MethodologyScore objects sorted by specified field
    """
    if rating_type not in ["ПУБЛИЧНЫЙ", "ЗАКРЫТЫЙ"]:
        raise HTTPException(status_code=400, detail="rating_type must be 'ПУБЛИЧНЫЙ' or 'ЗАКРЫТЫЙ'")

    try:
        # Get all municipalities
        municipalities = db.query(DimMO).all()

        scores = []
        for mo in municipalities:
            score = calculate_methodology_score(db, mo.mo_id, period_id, rating_type)
            if score:
                scores.append(score)

        # Sort results
        if sort == "score_total":
            scores.sort(key=lambda x: x.total_score, reverse=(order == "desc"))
        elif sort == "mo_name":
            scores.sort(key=lambda x: x.mo_name, reverse=(order == "desc"))
        elif sort == "leader_name":
            scores.sort(key=lambda x: x.leader_name or "", reverse=(order == "desc"))

        return {
            "period_id": period_id,
            "rating_type": rating_type,
            "total_municipalities": len(scores),
            "scores": scores
        }

    except Exception as e:
        logger.error(f"Error getting all methodology scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/methodology/risk-zones")
async def get_risk_zones_reference():
    """
    Get reference information about risk zones in the official methodology.

    Returns:
    - List of RiskZone objects with definitions
    """
    return {
        "zones": [
            {
                "zone_name": "Зелёная",
                "score_range": "53-66",
                "status": "High Stability",
                "assessment": "Resignation unlikely, significant resources for management & career growth",
                "color": "green"
            },
            {
                "zone_name": "Жёлтая",
                "score_range": "29-52",
                "status": "Conditional Stability",
                "assessment": "Risks exist, requires correction of management/political strategy",
                "color": "yellow"
            },
            {
                "zone_name": "Красная",
                "score_range": "0-28",
                "status": "Low Stability",
                "assessment": "High risk of resignation in medium-term, serious systemic problems",
                "color": "red"
            }
        ]
    }


@router.get("/methodology/info")
async def get_methodology_info(db: Session = Depends(get_db)):
    """
    Get comprehensive information about the official methodology structure.

    Returns:
    - Information about criteria, blocks, and point scales
    """
    # Get all official criteria grouped by rating type
    public_criteria = db.query(DimIndicator).filter(
        DimIndicator.rating_type == "ПУБЛИЧНЫЙ"
    ).all()

    closed_criteria = db.query(DimIndicator).filter(
        DimIndicator.rating_type == "ЗАКРЫТЫЙ"
    ).all()

    penalty_criteria = db.query(DimIndicator).filter(
        DimIndicator.is_penalty == True
    ).all()

    # Calculate totals
    public_max = sum(ind.max_points or 0 for ind in public_criteria)
    closed_max = sum(ind.max_points or 0 for ind in closed_criteria)
    penalty_max = sum(ind.max_points or 0 for ind in penalty_criteria)

    return {
        "methodology": "Official Methodology for Rating Municipal Heads",
        "version": "2.0",
        "document_source": "Методика оценки эффективности деятельности глав администраций МО 23.10.pdf",
        "ratings": {
            "public": {
                "name": "ПУБЛИЧНЫЙ РЕЙТИНГ",
                "criteria_count": len(public_criteria),
                "max_points": public_max,
                "criteria": [
                    {
                        "code": c.code,
                        "name": c.name,
                        "block": c.block,
                        "max_points": c.max_points,
                        "description": c.description
                    }
                    for c in public_criteria
                ]
            },
            "closed": {
                "name": "ЗАКРЫТЫЙ РЕЙТИНГ",
                "criteria_count": len(closed_criteria),
                "max_points": closed_max,
                "criteria": [
                    {
                        "code": c.code,
                        "name": c.name,
                        "block": c.block,
                        "max_points": c.max_points,
                        "description": c.description
                    }
                    for c in closed_criteria
                ]
            },
            "penalties": {
                "name": "ШТРАФНЫЕ КРИТЕРИИ",
                "criteria_count": len(penalty_criteria),
                "max_penalty": penalty_max,
                "criteria": [
                    {
                        "code": c.code,
                        "name": c.name,
                        "block": c.block,
                        "max_points": c.max_points,
                        "description": c.description
                    }
                    for c in penalty_criteria
                ]
            }
        },
        "risk_zones": {
            "green": {"range": "53-66", "status": "High Stability"},
            "yellow": {"range": "29-52", "status": "Conditional Stability"},
            "red": {"range": "0-28", "status": "Low Stability"}
        }
    }
