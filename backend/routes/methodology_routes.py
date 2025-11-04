from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from database import get_db
from models import DimMethodology, MapScale

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/versions")
async def get_methodology_versions(db: Session = Depends(get_db)):
    """Get all methodology versions"""
    try:
        versions = db.query(DimMethodology).order_by(
            DimMethodology.valid_from.desc()
        ).all()

        return {
            "status": "success",
            "count": len(versions),
            "data": [
                {
                    "version_id": v.version_id,
                    "version": v.version,
                    "valid_from": v.valid_from.isoformat() if v.valid_from else None,
                    "valid_to": v.valid_to.isoformat() if v.valid_to else None,
                    "notes": v.notes,
                }
                for v in versions
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching methodology versions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching versions")


@router.get("/{version_id}/scales")
async def get_scales(version_id: int, db: Session = Depends(get_db)):
    """Get scales (shading/zones) for a specific methodology version"""
    try:
        scales = db.query(MapScale).filter(
            MapScale.version_id == version_id
        ).all()

        if not scales:
            raise HTTPException(status_code=404, detail="Scales not found")

        return {
            "status": "success",
            "version_id": version_id,
            "count": len(scales),
            "data": [
                {
                    "scale_id": s.scale_id,
                    "zone": s.zone,
                    "min_score": float(s.min_score) if s.min_score else 0,
                    "max_score": float(s.max_score) if s.max_score else 0,
                    "color_hex": s.color_hex,
                    "ind_id": s.ind_id,
                    "pen_id": s.pen_id,
                }
                for s in scales
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scales: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching scales")
