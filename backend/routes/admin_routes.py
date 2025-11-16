"""
Admin routes - For managing rating data (leaders, indicators, penalties)
"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text
import csv
import io
import logging

from database import get_db
from models import DimMO, DimIndicator, FactIndicator, DimPeriod, DimMethodology

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/upload-leader-names")
async def upload_leader_names(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload leader names from CSV file

    CSV format:
    МО,ФИО главы
    Липецк,Ченцов Р.И.
    Елец,Жабин В.П.
    ...
    """
    try:
        # Read CSV file
        contents = await file.read()
        csv_reader = csv.DictReader(
            io.StringIO(contents.decode('utf-8')),
            fieldnames=['МО', 'ФИО главы']
        )

        updated_count = 0
        for row in csv_reader:
            if row['МО'] and row['ФИО главы']:
                mo_name = row['МО'].strip()
                leader_name = row['ФИО главы'].strip()

                # Update MO with leader name
                db.query(DimMO).filter(
                    DimMO.mo_name.ilike(f"%{mo_name}%")
                ).update({DimMO.leader_name: leader_name})
                updated_count += 1

        db.commit()

        return {
            "status": "success",
            "message": f"Updated {updated_count} leader names",
            "updated_count": updated_count,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading leader names: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.post("/populate-test-data")
async def populate_test_data(period: str = "2024-01", db: Session = Depends(get_db)):
    """
    Populate database with test indicator and penalty data
    Format: YYYY-MM (e.g., 2024-01)
    """
    try:
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        # Parse period
        try:
            period_date = datetime.strptime(period, "%Y-%m").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid period format. Use YYYY-MM")

        # Get or create period
        period_obj = db.query(DimPeriod).filter(
            DimPeriod.date_from <= period_date,
            DimPeriod.date_to >= period_date,
        ).first()

        if not period_obj:
            # Create new period
            period_to = period_date + relativedelta(months=1, days=-1)
            period_obj = DimPeriod(
                period_type='month',
                date_from=period_date,
                date_to=period_to,
                edg_flag=False
            )
            db.add(period_obj)
            db.flush()

        # Get or create methodology
        methodology = db.query(DimMethodology).filter(
            DimMethodology.version == 'v1.0'
        ).first()

        if not methodology:
            methodology = DimMethodology(
                version='v1.0',
                valid_from=period_date,
                notes='Test methodology'
            )
            db.add(methodology)
            db.flush()

        # Get all indicators
        indicators = db.query(DimIndicator).all()

        # Get all MOs
        mos = db.query(DimMO).all()

        inserted_count = 0

        # Insert test data for each MO and indicator
        for mo in mos:
            for idx, indicator in enumerate(indicators):
                # Check if already exists
                existing = db.query(FactIndicator).filter(
                    FactIndicator.mo_id == mo.mo_id,
                    FactIndicator.period_id == period_obj.period_id,
                    FactIndicator.ind_id == indicator.ind_id,
                    FactIndicator.version_id == methodology.version_id,
                ).first()

                if not existing:
                    # Generate test score (varies by MO and indicator)
                    base_score = (mo.mo_id * 7 + idx * 13) % 100
                    score = (base_score / 100) * 10  # Scale to 0-10

                    fact = FactIndicator(
                        mo_id=mo.mo_id,
                        period_id=period_obj.period_id,
                        ind_id=indicator.ind_id,
                        version_id=methodology.version_id,
                        value_raw=score,
                        value_norm=score,
                        score=score,
                    )
                    db.add(fact)
                    inserted_count += 1

        db.commit()

        return {
            "status": "success",
            "message": f"Populated test data for period {period}",
            "inserted_records": inserted_count,
            "mos_count": len(mos),
            "indicators_count": len(indicators),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error populating test data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/leader-names-template")
async def get_leader_names_template():
    """
    Get CSV template for uploading leader names
    """
    template = """МО,ФИО главы
Липецк,Ченцов Р.И.
Елец,Жабин В.П.
Воловский,Щеглов С.С.
Грязянский,Рощупкин В.Т.
Данковский,Фалеев В.И.
Добринский,Пасынков А.Н.
Добровский,Попов А.А.
Долгоруковский,Тимохин А.Н.
Елецкий,Семенихин О.Н.
Задонский,Щедров А.И.
Измалковский,Иванников В.Ю.
Краснинский,Поляков С.О.
Лебедянский,Телков А.М.
Лев-Толстовский,Шабанов К.Ю.
Липецкий,Тодуа Д.В.
Становлянский,Семянников Д.Ю.
Тербунский,Черников Н.Е.
Усманский,Мазо В.М.
Хлевенский,Плотников А.И.
Чаплыгинский,Сазонов Ю.А."""

    return {
        "status": "success",
        "template": template,
        "format": "CSV with columns: МО, ФИО главы",
        "instructions": "Download this template, fill in the leader names, upload via /admin/upload-leader-names"
    }


@router.get("/db-status")
async def check_database_status(db: Session = Depends(get_db)):
    """
    Check current database status and data
    """
    try:
        # Count records in each table
        mo_count = db.query(DimMO).count()
        leaders_count = db.query(DimMO).filter(DimMO.leader_name.isnot(None)).count()
        indicator_count = db.query(DimIndicator).count()
        period_count = db.query(DimPeriod).count()
        fact_indicator_count = db.query(FactIndicator).count()

        return {
            "status": "success",
            "database_status": {
                "total_mos": mo_count,
                "mos_with_leaders": leaders_count,
                "total_indicators": indicator_count,
                "total_periods": period_count,
                "fact_indicators_records": fact_indicator_count,
            },
            "needs": {
                "leader_names": leaders_count < mo_count,
                "indicator_data": fact_indicator_count == 0,
            }
        }

    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
