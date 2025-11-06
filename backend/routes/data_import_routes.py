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
