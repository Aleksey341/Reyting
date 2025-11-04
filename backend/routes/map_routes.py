from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime
import logging

from database import get_db
from models import DimMO, FactSummary, DimPeriod, DimMethodology

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def get_map_data(
    period: Optional[str] = Query(None, description="Period in YYYY-MM format"),
    version: Optional[int] = Query(None, description="Methodology version ID"),
    db: Session = Depends(get_db),
):
    """
    Get map data with MO scores and zones.
    Returns GeoJSON-compatible features for map visualization.
    """
    try:
        query = db.query(
            DimMO.mo_id,
            DimMO.mo_name,
            DimMO.lat,
            DimMO.lon,
            FactSummary.score_total,
            FactSummary.zone,
        ).outerjoin(
            FactSummary,
            and_(
                DimMO.mo_id == FactSummary.mo_id,
                DimMO.mo_id == FactSummary.mo_id,
            )
        )

        if period:
            # Find period by date string
            period_date = datetime.strptime(period, "%Y-%m").date()
            period_obj = db.query(DimPeriod).filter(
                and_(
                    DimPeriod.date_from <= period_date,
                    DimPeriod.date_to >= period_date,
                )
            ).first()

            if period_obj:
                query = query.filter(FactSummary.period_id == period_obj.period_id)

        if version:
            query = query.filter(FactSummary.version_id == version)

        results = query.all()

        # Format response
        features = []
        for mo_id, mo_name, lat, lon, score, zone in results:
            features.append({
                "mo_id": mo_id,
                "mo_name": mo_name,
                "lat": float(lat) if lat else None,
                "lon": float(lon) if lon else None,
                "score_total": float(score) if score else 0,
                "zone": zone or "red",
            })

        return {
            "status": "success",
            "count": len(features),
            "data": features,
        }

    except Exception as e:
        logger.error(f"Error fetching map data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching map data")


@router.get("/{mo_id}")
async def get_mo_details(
    mo_id: int,
    period: Optional[str] = Query(None),
    version: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific MO (municipal organization).
    Includes summary scores and trend data.
    """
    try:
        mo = db.query(DimMO).filter(DimMO.mo_id == mo_id).first()
        if not mo:
            raise HTTPException(status_code=404, detail="MO not found")

        # Get summaries
        summary_query = db.query(FactSummary).filter(FactSummary.mo_id == mo_id)

        if period:
            period_date = datetime.strptime(period, "%Y-%m").date()
            period_obj = db.query(DimPeriod).filter(
                and_(
                    DimPeriod.date_from <= period_date,
                    DimPeriod.date_to >= period_date,
                )
            ).first()
            if period_obj:
                summary_query = summary_query.filter(
                    FactSummary.period_id == period_obj.period_id
                )

        if version:
            summary_query = summary_query.filter(FactSummary.version_id == version)

        summaries = summary_query.all()

        return {
            "status": "success",
            "mo_id": mo.mo_id,
            "mo_name": mo.mo_name,
            "lat": float(mo.lat) if mo.lat else None,
            "lon": float(mo.lon) if mo.lon else None,
            "population": mo.population,
            "area_km2": float(mo.area_km2) if mo.area_km2 else None,
            "summaries": [
                {
                    "score_public": float(s.score_public) if s.score_public else 0,
                    "score_closed": float(s.score_closed) if s.score_closed else 0,
                    "score_penalties": float(s.score_penalties) if s.score_penalties else 0,
                    "score_total": float(s.score_total) if s.score_total else 0,
                    "zone": s.zone,
                    "period_id": s.period_id,
                }
                for s in summaries
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching MO details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching MO details")
