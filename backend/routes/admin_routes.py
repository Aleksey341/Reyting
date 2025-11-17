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


@router.post("/load-official-methodology-data")
async def load_official_methodology_data(db: Session = Depends(get_db)):
    """
    Load official methodology data (18 criteria × 20 municipalities = 360 records).

    This endpoint executes the same SQL that load_official_data.sql contains.
    It populates fact_indicator with official methodology scores for all municipalities.

    After this, restart the app so calculate_fact_summary_from_indicators()
    migration runs and populates fact_summary with aggregated scores.
    """
    try:
        logger.info("🔄 Loading official methodology data...")

        period_id = 1  # Default period
        inserted_count = 0

        # Get official indicators and municipality data
        pub_indicators = db.query(DimIndicator).filter(
            DimIndicator.rating_type == 'ПУБЛИЧНЫЙ'
        ).all()

        closed_indicators = db.query(DimIndicator).filter(
            DimIndicator.rating_type == 'ЗАКРЫТЫЙ'
        ).all()

        penalty_indicators = db.query(DimIndicator).filter(
            DimIndicator.is_penalty == True
        ).all()

        municipalities = db.query(DimMO).all()

        logger.info(f"  Found {len(pub_indicators)} PUBLIC indicators")
        logger.info(f"  Found {len(closed_indicators)} CLOSED indicators")
        logger.info(f"  Found {len(penalty_indicators)} PENALTY indicators")
        logger.info(f"  Found {len(municipalities)} municipalities")

        # Data for all municipalities (from CSV analysis)
        municipality_data = {
            'Липецк': {'pub_2': 0.95, 'pub_3': 3, 'pub_4': 3, 'pub_5': 1.56, 'pub_6': 1.65, 'pub_7': 3, 'pub_8': 3, 'pub_9': 3,
                      'closed_1': 6, 'closed_2': 4, 'closed_3': 5, 'closed_4': 5, 'closed_5': 1, 'closed_7': 6, 'closed_8': 2,
                      'pen_1': 0, 'pen_2': -2, 'pen_3': -5},
            'Елец': {'pub_2': 0.88, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.44, 'pub_6': 1.53, 'pub_7': 3, 'pub_8': 2, 'pub_9': 1,
                    'closed_1': 5, 'closed_2': 3.8, 'closed_3': 3, 'closed_4': 3, 'closed_5': 1, 'closed_7': 3, 'closed_8': 2,
                    'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Воловский': {'pub_2': 0.76, 'pub_3': 0, 'pub_4': 1, 'pub_5': 0.84, 'pub_6': 0.9, 'pub_7': 1, 'pub_8': 1, 'pub_9': 0,
                         'closed_1': 1, 'closed_2': 3.76, 'closed_3': 0, 'closed_4': 0, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                         'pen_1': 0, 'pen_2': 0, 'pen_3': 0},
            'Грязянский': {'pub_2': 0.91, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.05, 'pub_6': 1.14, 'pub_7': 2, 'pub_8': 2, 'pub_9': 3,
                          'closed_1': 3, 'closed_2': 3.84, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 2, 'closed_8': 2,
                          'pen_1': 0, 'pen_2': -2, 'pen_3': 0},
            'Данковский': {'pub_2': 0.65, 'pub_3': 0, 'pub_4': 0, 'pub_5': 0.96, 'pub_6': 1.02, 'pub_7': 1, 'pub_8': 1, 'pub_9': 1,
                          'closed_1': 1, 'closed_2': 3.52, 'closed_3': 3, 'closed_4': 3, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                          'pen_1': -3, 'pen_2': -3, 'pen_3': -5},
            'Добринский': {'pub_2': 0.82, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.23, 'pub_6': 1.29, 'pub_7': 2, 'pub_8': 2, 'pub_9': 3,
                          'closed_1': 4, 'closed_2': 3.72, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 3, 'closed_8': 2,
                          'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Добровский': {'pub_2': 0.71, 'pub_3': 0, 'pub_4': 1, 'pub_5': 1.14, 'pub_6': 1.2, 'pub_7': 2, 'pub_8': 2, 'pub_9': 0,
                          'closed_1': 1, 'closed_2': 3.6, 'closed_3': 3, 'closed_4': 3, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                          'pen_1': 0, 'pen_2': -2, 'pen_3': 0},
            'Долгоруковский': {'pub_2': 0.93, 'pub_3': 3, 'pub_4': 3, 'pub_5': 1.5, 'pub_6': 1.56, 'pub_7': 3, 'pub_8': 2, 'pub_9': 3,
                              'closed_1': 4, 'closed_2': 3.88, 'closed_3': 5, 'closed_4': 5, 'closed_5': 1, 'closed_7': 3, 'closed_8': 2,
                              'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Елецкий': {'pub_2': 0.58, 'pub_3': 0, 'pub_4': 0, 'pub_5': 0.87, 'pub_6': 0.93, 'pub_7': 1, 'pub_8': 1, 'pub_9': 0,
                       'closed_1': 1, 'closed_2': 3.4, 'closed_3': 0, 'closed_4': 0, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                       'pen_1': 0, 'pen_2': -3, 'pen_3': -5},
            'Задонский': {'pub_2': 0.79, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.35, 'pub_6': 1.41, 'pub_7': 2, 'pub_8': 2, 'pub_9': 3,
                         'closed_1': 3, 'closed_2': 3.68, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 2, 'closed_8': 2,
                         'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Измалковский': {'pub_2': 0.85, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.41, 'pub_6': 1.47, 'pub_7': 3, 'pub_8': 2, 'pub_9': 3,
                            'closed_1': 3, 'closed_2': 3.8, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 2, 'closed_8': 2,
                            'pen_1': 0, 'pen_2': 0, 'pen_3': 0},
            'Краснинский': {'pub_2': 0.68, 'pub_3': 0, 'pub_4': 1, 'pub_5': 0.9, 'pub_6': 0.96, 'pub_7': 1, 'pub_8': 1, 'pub_9': 1,
                           'closed_1': 1, 'closed_2': 3.48, 'closed_3': 3, 'closed_4': 3, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                           'pen_1': 0, 'pen_2': -2, 'pen_3': -5},
            'Лебедянский': {'pub_2': 0.77, 'pub_3': 3, 'pub_4': 1, 'pub_5': 1.26, 'pub_6': 1.32, 'pub_7': 2, 'pub_8': 2, 'pub_9': 0,
                           'closed_1': 2, 'closed_2': 3.64, 'closed_3': 3, 'closed_4': 3, 'closed_5': 2, 'closed_7': 2, 'closed_8': 0,
                           'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Лев-Толстовский': {'pub_2': 0.81, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.38, 'pub_6': 1.44, 'pub_7': 3, 'pub_8': 2, 'pub_9': 3,
                               'closed_1': 4, 'closed_2': 3.76, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 3, 'closed_8': 2,
                               'pen_1': 0, 'pen_2': 0, 'pen_3': 0},
            'Липецкий': {'pub_2': 0.9, 'pub_3': 3, 'pub_4': 3, 'pub_5': 1.53, 'pub_6': 1.59, 'pub_7': 3, 'pub_8': 2, 'pub_9': 3,
                        'closed_1': 6, 'closed_2': 3.96, 'closed_3': 5, 'closed_4': 5, 'closed_5': 1, 'closed_7': 6, 'closed_8': 2,
                        'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Становлянский': {'pub_2': 0.73, 'pub_3': 0, 'pub_4': 1, 'pub_5': 0.99, 'pub_6': 1.05, 'pub_7': 1, 'pub_8': 1, 'pub_9': 1,
                             'closed_1': 1, 'closed_2': 3.56, 'closed_3': 3, 'closed_4': 3, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                             'pen_1': -3, 'pen_2': -3, 'pen_3': 0},
            'Тербунский': {'pub_2': 0.69, 'pub_3': 0, 'pub_4': 1, 'pub_5': 0.93, 'pub_6': 0.99, 'pub_7': 1, 'pub_8': 1, 'pub_9': 1,
                          'closed_1': 1, 'closed_2': 3.44, 'closed_3': 0, 'closed_4': 0, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                          'pen_1': 0, 'pen_2': -4, 'pen_3': 0},
            'Усманский': {'pub_2': 0.84, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.32, 'pub_6': 1.38, 'pub_7': 2, 'pub_8': 2, 'pub_9': 2,
                         'closed_1': 3, 'closed_2': 3.72, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 2, 'closed_8': 2,
                         'pen_1': 0, 'pen_2': -1, 'pen_3': 0},
            'Хлевенский': {'pub_2': 0.75, 'pub_3': 0, 'pub_4': 1, 'pub_5': 1.11, 'pub_6': 1.17, 'pub_7': 2, 'pub_8': 2, 'pub_9': 1,
                          'closed_1': 2, 'closed_2': 3.6, 'closed_3': 3, 'closed_4': 3, 'closed_5': 3, 'closed_7': 1, 'closed_8': 0,
                          'pen_1': 0, 'pen_2': -2, 'pen_3': 0},
            'Чаплыгинский': {'pub_2': 0.86, 'pub_3': 3, 'pub_4': 2, 'pub_5': 1.47, 'pub_6': 1.53, 'pub_7': 3, 'pub_8': 2, 'pub_9': 3,
                            'closed_1': 4, 'closed_2': 3.84, 'closed_3': 5, 'closed_4': 5, 'closed_5': 2, 'closed_7': 3, 'closed_8': 2,
                            'pen_1': 0, 'pen_2': 0, 'pen_3': 0},
        }

        # Insert data for each municipality and criterion
        for mo_name, scores in municipality_data.items():
            mo = db.query(DimMO).filter(DimMO.mo_name == mo_name).first()
            if not mo:
                logger.warning(f"  ⚠️  MO not found: {mo_name}")
                continue

            for criterion_code, score in scores.items():
                # Find the indicator
                indicator = db.query(DimIndicator).filter(
                    DimIndicator.code == criterion_code
                ).first()

                if not indicator:
                    logger.warning(f"  ⚠️  Indicator not found: {criterion_code}")
                    continue

                # Check if already exists
                existing = db.query(FactIndicator).filter(
                    FactIndicator.mo_id == mo.mo_id,
                    FactIndicator.ind_id == indicator.ind_id,
                    FactIndicator.period_id == period_id,
                ).first()

                if not existing:
                    fact = FactIndicator(
                        mo_id=mo.mo_id,
                        ind_id=indicator.ind_id,
                        period_id=period_id,
                        score=score,
                    )
                    db.add(fact)
                    inserted_count += 1

        db.commit()
        logger.info(f"  ✅ Inserted {inserted_count} indicator records")

        return {
            "status": "success",
            "message": "Official methodology data loaded successfully!",
            "inserted_records": inserted_count,
            "next_steps": [
                "1. Restart the application so migrations run",
                "2. Migration calculate_fact_summary_from_indicators() will populate fact_summary",
                "3. Hard refresh Rating tab (Ctrl+F5)",
                "4. Scores should display instead of zeros"
            ]
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error loading official methodology data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
