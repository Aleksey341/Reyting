"""
API routes for importing CSV data
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import pandas as pd
import io

from database import get_db
from models import DimMO, DimPeriod, DimIndicator, DimMethodology, FactIndicator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Import CSV file with indicator data.
    Expected format: CSV with columns including 'Муниципалитет' and various indicators.
    """
    try:
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8')

        logger.info(f"CSV uploaded: {len(df)} rows, {len(df.columns)} columns")

        # Create or get methodology v1
        methodology = db.query(DimMethodology).filter(
            DimMethodology.version == "v1"
        ).first()

        if not methodology:
            methodology = DimMethodology(
                version="v1",
                valid_from="2024-01-01",
                notes="Оценка поддержки руководителя v1"
            )
            db.add(methodology)
            db.commit()
            db.refresh(methodology)
            logger.info(f"Created methodology v1 (ID: {methodology.version_id})")

        # Create or get period 2024-01
        period = db.query(DimPeriod).filter(
            DimPeriod.date_from == "2024-01-01"
        ).first()

        if not period:
            period = DimPeriod(
                period_type="month",
                date_from="2024-01-01",
                date_to="2024-01-31",
                edg_flag=False
            )
            db.add(period)
            db.commit()
            db.refresh(period)
            logger.info(f"Created period 2024-01 (ID: {period.period_id})")

        # Create municipalities
        municipalities = df[['Муниципалитет']].drop_duplicates()
        mo_created = 0

        for _, row in municipalities.iterrows():
            mo_name = row['Муниципалитет']
            if pd.isna(mo_name) or mo_name == '':
                continue

            existing = db.query(DimMO).filter(DimMO.mo_name == mo_name).first()
            if not existing:
                mo = DimMO(
                    mo_name=mo_name,
                    type="Муниципальный район"
                )
                db.add(mo)
                mo_created += 1

        db.commit()
        logger.info(f"Created {mo_created} municipalities")

        # Create indicators
        skip_columns = ['Лист', 'Муниципалитет', 'Глава МО']
        indicator_columns = [col for col in df.columns if col not in skip_columns]

        ind_created = 0
        for col_name in indicator_columns:
            code = col_name[:50].replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')

            existing = db.query(DimIndicator).filter(DimIndicator.code == code).first()
            if not existing:
                indicator = DimIndicator(
                    code=code,
                    name=col_name,
                    block="Оценка поддержки руководителя",
                    is_public=True
                )
                db.add(indicator)
                ind_created += 1

        db.commit()
        logger.info(f"Created {ind_created} indicators")

        # Load indicator values
        mo_map = {mo.mo_name: mo.mo_id for mo in db.query(DimMO).all()}
        ind_map = {ind.name: ind.ind_id for ind in db.query(DimIndicator).all()}

        values_loaded = 0
        errors = 0

        for _, row in df.iterrows():
            mo_name = row['Муниципалитет']
            if pd.isna(mo_name) or mo_name == '' or mo_name not in mo_map:
                continue

            mo_id = mo_map[mo_name]

            for col_name in indicator_columns:
                value = row[col_name]
                if pd.isna(value) or value == '':
                    continue

                if col_name not in ind_map:
                    continue

                ind_id = ind_map[col_name]

                # Convert value to float
                try:
                    if isinstance(value, str):
                        value_clean = value.replace('%', '').replace(' ', '').replace(',', '.')
                        try:
                            value_raw = float(value_clean)
                        except:
                            value_raw = 1.0
                    else:
                        value_raw = float(value)
                except:
                    value_raw = 1.0

                # Check if exists
                existing = db.query(FactIndicator).filter(
                    FactIndicator.mo_id == mo_id,
                    FactIndicator.period_id == period.period_id,
                    FactIndicator.ind_id == ind_id,
                    FactIndicator.version_id == methodology.version_id
                ).first()

                if existing:
                    existing.value_raw = value_raw
                else:
                    fact = FactIndicator(
                        mo_id=mo_id,
                        period_id=period.period_id,
                        ind_id=ind_id,
                        version_id=methodology.version_id,
                        value_raw=value_raw
                    )
                    db.add(fact)

                values_loaded += 1

        db.commit()
        logger.info(f"Loaded {values_loaded} indicator values")

        return {
            "status": "success",
            "message": "CSV imported successfully",
            "statistics": {
                "rows": len(df),
                "columns": len(df.columns),
                "municipalities_created": mo_created,
                "indicators_created": ind_created,
                "values_loaded": values_loaded
            }
        }

    except Exception as e:
        logger.error(f"Error importing CSV: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")


@router.get("/stats")
async def get_import_stats(db: Session = Depends(get_db)):
    """Get current database statistics"""
    try:
        stats = {
            "municipalities": db.query(DimMO).count(),
            "indicators": db.query(DimIndicator).count(),
            "periods": db.query(DimPeriod).count(),
            "methodologies": db.query(DimMethodology).count(),
            "indicator_values": db.query(FactIndicator).count(),
        }

        return {
            "status": "success",
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.post("/update-coordinates")
async def update_municipality_coordinates(db: Session = Depends(get_db)):
    """
    Update coordinates for Lipetsk Oblast municipalities.
    Adds lat/lon for map visualization.
    """
    try:
        # Coordinates for Lipetsk Oblast municipalities (approximate centers)
        coordinates = {
            "Липецк": (52.6031, 39.5708),
            "Елец": (52.6236, 38.5019),
            "Воловский": (51.1528, 38.4500),
            "Грязянский": (52.5000, 39.9500),
            "Данковский": (53.2500, 39.1500),
            "Добринский": (52.2000, 40.4000),
            "Добровский": (52.3500, 39.2000),
            "Долгоруковский": (52.3500, 38.3000),
            "Елецкий": (52.6236, 38.5019),
            "Задонский": (52.4000, 38.9000),
            "Измалковский": (52.5000, 38.8000),
            "Краснинский": (53.0000, 39.5000),
            "Лебедянский": (53.0200, 39.1300),
            "Лев-Толстовский": (52.1000, 39.5000),
            "Липецкий": (52.6031, 39.5708),
            "Становлянский": (53.0000, 38.5000),
            "Тербунский": (52.1500, 38.2500),
            "Усманский": (52.0500, 39.7400),
            "Хлевенский": (52.4500, 38.1000),
            "Чаплыгинский": (53.2500, 39.9500),
        }

        updated = 0
        for mo_name, (lat, lon) in coordinates.items():
            mo = db.query(DimMO).filter(DimMO.mo_name == mo_name).first()
            if mo:
                mo.lat = lat
                mo.lon = lon
                updated += 1

        db.commit()
        logger.info(f"Updated coordinates for {updated} municipalities")

        return {
            "status": "success",
            "message": f"Updated coordinates for {updated} municipalities",
            "updated": updated
        }

    except Exception as e:
        logger.error(f"Error updating coordinates: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating coordinates: {str(e)}")


@router.post("/migrate-add-geojson")
async def migrate_add_geojson_column(db: Session = Depends(get_db)):
    """
    Add geojson column to dim_mo table if it doesn't exist.
    This is a one-time migration.
    """
    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='dim_mo' AND column_name='geojson'
        """))

        if result.fetchone() is None:
            # Add column
            db.execute(text("ALTER TABLE dim_mo ADD COLUMN geojson JSON"))
            db.commit()
            logger.info("Added geojson column to dim_mo table")
            return {
                "status": "success",
                "message": "geojson column added to dim_mo table"
            }
        else:
            return {
                "status": "success",
                "message": "geojson column already exists"
            }

    except Exception as e:
        logger.error(f"Error adding geojson column: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding geojson column: {str(e)}")


@router.post("/update-geojson")
async def update_municipality_geojson(db: Session = Depends(get_db)):
    """
    Update GeoJSON boundaries for Lipetsk Oblast municipalities.
    For now, this generates simplified polygon boundaries based on coordinates.
    In production, this should be replaced with real GeoJSON data from OpenStreetMap or similar.
    """
    try:
        municipalities = db.query(DimMO).all()
        updated = 0

        for mo in municipalities:
            if mo.lat and mo.lon:
                # Generate a more realistic polygon (hexagon instead of rectangle)
                # This is still simplified - real boundaries should come from OSM
                size = 0.15
                lat, lon = mo.lat, mo.lon

                # Create a hexagon-like shape
                import math
                points = []
                for i in range(6):
                    angle = (i * 60) * (math.pi / 180)
                    point_lon = lon + size * math.cos(angle)
                    point_lat = lat + size * math.sin(angle)
                    points.append([point_lon, point_lat])

                # Close the polygon
                points.append(points[0])

                # GeoJSON Polygon format
                geojson_data = {
                    "type": "Polygon",
                    "coordinates": [points]
                }

                mo.geojson = geojson_data
                updated += 1

        db.commit()
        logger.info(f"Updated GeoJSON for {updated} municipalities")

        return {
            "status": "success",
            "message": f"Updated GeoJSON for {updated} municipalities",
            "updated": updated,
            "note": "Using generated hexagon boundaries. Replace with real OSM data for production."
        }

    except Exception as e:
        logger.error(f"Error updating GeoJSON: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating GeoJSON: {str(e)}")


@router.post("/calculate-scores")
async def calculate_summary_scores(db: Session = Depends(get_db)):
    """
    Calculate summary scores for all municipalities.
    Creates records in fact_summary table based on indicator values.
    """
    try:
        from models import FactSummary

        # Get all municipalities
        municipalities = db.query(DimMO).all()

        # Get period and methodology
        period = db.query(DimPeriod).filter(DimPeriod.date_from == "2024-01-01").first()
        methodology = db.query(DimMethodology).filter(DimMethodology.version == "v1").first()

        if not period or not methodology:
            raise HTTPException(status_code=404, detail="Period or methodology not found")

        created = 0
        updated = 0

        for mo in municipalities:
            # Get all indicator values for this MO
            indicator_values = db.query(FactIndicator).filter(
                FactIndicator.mo_id == mo.mo_id,
                FactIndicator.period_id == period.period_id,
                FactIndicator.version_id == methodology.version_id
            ).all()

            if not indicator_values:
                continue

            # Calculate simple average score (можно сделать более сложную логику)
            total_values = sum([v.value_raw for v in indicator_values if v.value_raw])
            count_values = len([v for v in indicator_values if v.value_raw])

            if count_values > 0:
                avg_score = total_values / count_values
                # Normalize to 0-100 scale
                score_total = min(100, max(0, avg_score))

                # Determine zone based on score
                if score_total >= 70:
                    zone = "green"
                elif score_total >= 40:
                    zone = "yellow"
                else:
                    zone = "red"
            else:
                score_total = 0
                zone = "red"

            # Check if summary exists
            existing = db.query(FactSummary).filter(
                FactSummary.mo_id == mo.mo_id,
                FactSummary.period_id == period.period_id,
                FactSummary.version_id == methodology.version_id
            ).first()

            if existing:
                existing.score_total = score_total
                existing.score_public = score_total
                existing.zone = zone
                updated += 1
            else:
                summary = FactSummary(
                    mo_id=mo.mo_id,
                    period_id=period.period_id,
                    version_id=methodology.version_id,
                    score_public=score_total,
                    score_total=score_total,
                    zone=zone
                )
                db.add(summary)
                created += 1

        db.commit()
        logger.info(f"Created {created} summaries, updated {updated}")

        return {
            "status": "success",
            "message": f"Calculated scores for municipalities",
            "created": created,
            "updated": updated
        }

    except Exception as e:
        logger.error(f"Error calculating scores: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")
