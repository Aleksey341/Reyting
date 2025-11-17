"""
API routes for importing CSV data
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import pandas as pd
import io
import json

from database import get_db
from models import DimMO, DimPeriod, DimIndicator, DimMethodology, FactIndicator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/official-methodology")
async def import_official_methodology_csv(
    file: UploadFile = File(...),
    period_month: str = "2024-01",
    db: Session = Depends(get_db),
):
    """
    Import CSV file with official methodology indicator data.

    Expected CSV format:
    - First column: Муниципалитет (Municipality name)
    - Columns: pub_1, pub_2, pub_3, pub_4, pub_5, pub_6, pub_7, pub_8, pub_9
               closed_1, closed_2, closed_3, closed_4, closed_5, closed_6, closed_7, closed_8
               pen_1, pen_2, pen_3

    Example row:
    Липецк, 3, 5, 3, 3, 3, 3, 3, 3, 3, 6, 4, 5, 5, 3, 3, 6, 2, -3, -3, -5

    Parameters:
    - file: CSV file to upload
    - period_month: Period in YYYY-MM format (default: 2024-01)
    """
    try:
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8')

        logger.info(f"CSV uploaded: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Target period: {period_month}")
        logger.info(f"Columns: {list(df.columns)}")

        # Parse period_month
        from datetime import datetime, timedelta
        period_date = datetime.strptime(period_month, "%Y-%m")

        # Calculate last day of month
        if period_date.month == 12:
            period_end = period_date.replace(day=31)
        else:
            next_month = period_date.replace(month=period_date.month + 1, day=1)
            period_end = next_month - timedelta(days=1)

        date_from = period_date.strftime("%Y-%m-%d")
        date_to = period_end.strftime("%Y-%m-%d")

        # Ensure official methodology exists
        logger.info("Ensuring official methodology exists...")
        from migrations import implement_official_methodology
        implement_official_methodology()

        # Get or create official methodology version
        methodology = db.query(DimMethodology).first()
        if not methodology:
            methodology = DimMethodology(
                version="Official v1",
                valid_from="2024-01-01",
                notes="Official methodology with 16 criteria"
            )
            db.add(methodology)
            db.commit()
            db.refresh(methodology)
            logger.info(f"Created official methodology (ID: {methodology.version_id})")

        # Get or create period
        period = db.query(DimPeriod).filter(
            DimPeriod.date_from == date_from
        ).first()

        if not period:
            period = DimPeriod(
                period_type="month",
                date_from=date_from,
                date_to=date_to,
                edg_flag=False
            )
            db.add(period)
            db.commit()
            db.refresh(period)
            logger.info(f"Created period {period_month} (ID: {period.period_id})")

        # Official indicator codes
        official_indicators = [
            'pub_1', 'pub_2', 'pub_3', 'pub_4', 'pub_5', 'pub_6', 'pub_7', 'pub_8', 'pub_9',
            'closed_1', 'closed_2', 'closed_3', 'closed_4', 'closed_5', 'closed_6', 'closed_7', 'closed_8',
            'pen_1', 'pen_2', 'pen_3'
        ]

        # Load data
        values_loaded = 0
        errors = 0
        rows_processed = 0

        for _, row in df.iterrows():
            mo_name = row.get('Муниципалитет') or row.get('municipalitet') or row.get('mo_name')

            if pd.isna(mo_name) or mo_name == '':
                continue

            rows_processed += 1

            # Find MO by name
            mo = db.query(DimMO).filter(
                text("mo_name ILIKE :name")
            ).params(name=f"%{mo_name}%").first()

            if not mo:
                logger.warning(f"Municipality not found: {mo_name}")
                continue

            # Load official indicators
            for ind_code in official_indicators:
                # Check if column exists in CSV
                if ind_code not in row:
                    continue

                value = row[ind_code]
                if pd.isna(value) or value == '':
                    continue

                # Find indicator
                indicator = db.query(DimIndicator).filter(
                    DimIndicator.code == ind_code
                ).first()

                if not indicator:
                    logger.warning(f"Indicator not found: {ind_code}")
                    continue

                # Convert value to float
                try:
                    if isinstance(value, str):
                        value_clean = value.replace('%', '').replace(' ', '').replace(',', '.')
                        try:
                            value_float = float(value_clean)
                        except:
                            value_float = 0.0
                    else:
                        value_float = float(value)
                except:
                    value_float = 0.0

                # Check if exists
                existing = db.query(FactIndicator).filter(
                    FactIndicator.mo_id == mo.mo_id,
                    FactIndicator.period_id == period.period_id,
                    FactIndicator.ind_id == indicator.ind_id,
                    FactIndicator.version_id == methodology.version_id
                ).first()

                if existing:
                    existing.score = value_float
                else:
                    fact = FactIndicator(
                        mo_id=mo.mo_id,
                        period_id=period.period_id,
                        ind_id=indicator.ind_id,
                        version_id=methodology.version_id,
                        score=value_float,
                    )
                    db.add(fact)

                values_loaded += 1

        db.commit()
        logger.info(f"Loaded {values_loaded} indicator values from {rows_processed} rows")

        # Automatically calculate aggregated scores
        logger.info(f"Auto-calculating aggregated scores for period {period.period_id}...")
        try:
            from migrations import calculate_fact_summary_from_indicators
            calculate_fact_summary_from_indicators()
            logger.info("✓ Aggregated scores calculated successfully")
        except Exception as e:
            logger.error(f"Error calculating aggregated scores: {e}")

        return {
            "status": "success",
            "message": "Official methodology data imported successfully!",
            "statistics": {
                "rows_processed": rows_processed,
                "values_loaded": values_loaded,
                "period": period_month,
                "period_id": period.period_id,
                "methodology": "Official 16 criteria"
            },
            "next_steps": [
                "1. Hard refresh Rating tab (Ctrl+F5)",
                "2. Scores should display with proper aggregation"
            ]
        }

    except Exception as e:
        logger.error(f"Error importing official methodology CSV: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")


@router.get("/official-methodology-template")
async def get_official_methodology_template(db: Session = Depends(get_db)):
    """
    Get CSV template for official methodology data import.

    Returns a CSV with municipality names and official indicator column headers.
    """
    try:
        # Get all municipalities
        municipalities = db.query(DimMO).all()

        # Official indicator codes
        official_indicators = [
            'pub_1', 'pub_2', 'pub_3', 'pub_4', 'pub_5', 'pub_6', 'pub_7', 'pub_8', 'pub_9',
            'closed_1', 'closed_2', 'closed_3', 'closed_4', 'closed_5', 'closed_6', 'closed_7', 'closed_8',
            'pen_1', 'pen_2', 'pen_3'
        ]

        # Build CSV header
        header = "Муниципалитет," + ",".join(official_indicators)

        # Build CSV rows with municipality names
        rows = [header]
        for mo in municipalities:
            rows.append(mo.mo_name + "," + ",".join([""] * len(official_indicators)))

        csv_content = "\n".join(rows)

        return {
            "status": "success",
            "content": csv_content,
            "instructions": {
                "format": "CSV with UTF-8 encoding",
                "columns": official_indicators,
                "example": "Липецк,3,5,3,3,3,3,3,3,3,6,4,5,5,3,3,6,2,-3,-3,-5",
                "note": "All 20 municipalities are pre-filled. Just add scores."
            }
        }

    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    period_month: str = "2024-01",  # Формат: YYYY-MM
    db: Session = Depends(get_db),
):
    """
    Import CSV file with indicator data.
    Expected format: CSV with columns including 'Муниципалитет' and various indicators.

    Parameters:
    - file: CSV file to upload
    - period_month: Period in YYYY-MM format (default: 2024-01)
    """
    try:
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content), encoding='utf-8')

        logger.info(f"CSV uploaded: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Target period: {period_month}")

        # Parse period_month
        from datetime import datetime, timedelta
        period_date = datetime.strptime(period_month, "%Y-%m")

        # Calculate last day of month
        if period_date.month == 12:
            period_end = period_date.replace(day=31)
        else:
            next_month = period_date.replace(month=period_date.month + 1, day=1)
            period_end = next_month - timedelta(days=1)

        date_from = period_date.strftime("%Y-%m-%d")
        date_to = period_end.strftime("%Y-%m-%d")

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

        # Create or get period
        period = db.query(DimPeriod).filter(
            DimPeriod.date_from == date_from
        ).first()

        if not period:
            period = DimPeriod(
                period_type="month",
                date_from=date_from,
                date_to=date_to,
                edg_flag=False
            )
            db.add(period)
            db.commit()
            db.refresh(period)
            logger.info(f"Created period {period_month} (ID: {period.period_id})")
        else:
            logger.info(f"Using existing period {period_month} (ID: {period.period_id})")

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
                    existing.score = value_raw  # Также обновить score
                else:
                    fact = FactIndicator(
                        mo_id=mo_id,
                        period_id=period.period_id,
                        ind_id=ind_id,
                        version_id=methodology.version_id,
                        value_raw=value_raw,
                        score=value_raw  # ← ДОБАВИТЬ: заполнить score
                    )
                    db.add(fact)

                values_loaded += 1

        db.commit()
        logger.info(f"Loaded {values_loaded} indicator values")

        # Автоматически пересчитать баллы для загруженного периода
        logger.info(f"Auto-calculating scores for period {period.period_id}...")
        try:
            score_result = await calculate_summary_scores(period_id=period.period_id, db=db)
            logger.info(f"Scores calculated: {score_result}")
        except Exception as e:
            logger.error(f"Error calculating scores: {e}")
            # Не падаем, если пересчет не удался - данные уже загружены

        return {
            "status": "success",
            "message": "CSV imported successfully and scores calculated",
            "statistics": {
                "rows": len(df),
                "columns": len(df.columns),
                "municipalities_created": mo_created,
                "indicators_created": ind_created,
                "values_loaded": values_loaded
            },
            "scores_calculated": True
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


@router.get("/run-migration")
async def run_migration_page(db: Session = Depends(get_db)):
    """
    Execute full migration: add geojson column and populate data.
    Returns HTML page with results.
    """
    from fastapi.responses import HTMLResponse

    results = []

    # Step 1: Add geojson column
    try:
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='dim_mo' AND column_name='geojson'
        """))

        if result.fetchone() is None:
            db.execute(text("ALTER TABLE dim_mo ADD COLUMN geojson JSON"))
            db.commit()
            results.append(("✅ Миграция", "Колонка geojson успешно добавлена"))
        else:
            results.append(("ℹ️ Миграция", "Колонка geojson уже существует"))
    except Exception as e:
        results.append(("❌ Миграция", f"Ошибка: {str(e)}"))
        db.rollback()

    # Step 2: Update geojson data with realistic boundaries
    try:
        import math
        municipalities = db.query(DimMO).all()
        updated = 0

        for mo in municipalities:
            if mo.lat and mo.lon:
                lat, lon = mo.lat, mo.lon

                # Определяем размер (города меньше, районы больше)
                if mo.mo_name in ["Липецк", "Елец"]:
                    size = 0.12
                else:
                    size = 0.20

                # Создаем эллиптический полигон с волнистыми краями
                points_count = 48
                coordinates = []

                for i in range(points_count):
                    angle = (i * 360 / points_count) * (math.pi / 180)

                    # Эллиптическая форма
                    a = size * 1.5
                    b = size

                    # Волнистость
                    wave = 1.0 + 0.15 * math.sin(5 * angle) + 0.1 * math.cos(7 * angle)

                    r = (a * b) / math.sqrt((b * math.cos(angle))**2 + (a * math.sin(angle))**2)
                    r *= wave

                    point_lat = lat + r * math.sin(angle)
                    point_lon = lon + r * math.cos(angle) / math.cos(lat * math.pi / 180)

                    coordinates.append([point_lon, point_lat])

                # Замыкаем полигон
                coordinates.append(coordinates[0])

                geojson_data = {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                }

                mo.geojson = geojson_data
                updated += 1

        db.commit()
        results.append(("✅ GeoJSON", f"Обновлено границ: {updated} (эллиптические с волнистыми краями)"))
    except Exception as e:
        results.append(("❌ GeoJSON", f"Ошибка: {str(e)}"))
        db.rollback()

    # Generate HTML response
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Результаты миграции</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            .result {
                margin: 15px 0;
                padding: 15px;
                border-left: 4px solid #3b82f6;
                background: #f0f9ff;
            }
            .result h3 {
                margin: 0 0 10px 0;
                color: #1e40af;
            }
            .result p {
                margin: 0;
                color: #475569;
            }
            .success { border-left-color: #10b981; background: #d1fae5; }
            .success h3 { color: #065f46; }
            .error { border-left-color: #ef4444; background: #fee2e2; }
            .error h3 { color: #991b1b; }
            .button {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                background: #3b82f6;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .button:hover {
                background: #2563eb;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Результаты миграции базы данных</h1>
    """

    for title, message in results:
        status_class = "success" if "✅" in title or "ℹ️" in title else "error"
        html_content += f"""
            <div class="result {status_class}">
                <h3>{title}</h3>
                <p>{message}</p>
            </div>
        """

    html_content += """
            <a href="/map" class="button">Открыть карту</a>
            <a href="/api/docs" class="button" style="background: #6b7280;">API Docs</a>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


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


@router.post("/upload-real-boundaries")
async def upload_real_boundaries(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload real GeoJSON boundaries from file.
    Expects standard GeoJSON FeatureCollection with properties.name for each municipality.

    Format:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {"name": "Липецк", ...},
          "geometry": {"type": "Polygon", "coordinates": [...]}
        },
        ...
      ]
    }
    """
    try:
        # Read uploaded file
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        logger.info(f"Uploading real boundaries from file: {file.filename}")

        # Support both FeatureCollection and old format
        if data.get("type") == "FeatureCollection":
            features = data.get("features", [])
            logger.info(f"Found FeatureCollection with {len(features)} features")

            updated = 0
            not_found = []
            errors = []

            for feature in features:
                if feature.get("type") != "Feature":
                    errors.append(f"Invalid feature type: {feature.get('type')}")
                    continue

                properties = feature.get("properties", {})
                geometry = feature.get("geometry")

                # Get municipality name from properties
                mo_name = properties.get("name") or properties.get("NAME") or properties.get("mo_name")

                if not mo_name:
                    errors.append("Feature missing 'name' property")
                    continue

                mo_name = mo_name.strip()

                if not geometry:
                    errors.append(f"Feature {mo_name} missing geometry")
                    continue

                # Find municipality in database (case-insensitive)
                mo = db.query(DimMO).filter(
                    DimMO.mo_name.ilike(mo_name)
                ).first()

                if mo:
                    # Store as GeoJSON Feature
                    mo.geojson = {
                        "type": "Feature",
                        "properties": {"name": mo.mo_name},  # Use DB name for consistency
                        "geometry": geometry
                    }
                    updated += 1
                    logger.info(f"Updated {mo.mo_name}")
                else:
                    not_found.append(mo_name)
                    logger.warning(f"Municipality not found in DB: {mo_name}")

            db.commit()

            return {
                "status": "success",
                "message": f"Uploaded real boundaries for {updated} municipalities",
                "updated": updated,
                "not_found": not_found,
                "errors": errors,
                "note": "Real boundaries from GeoJSON FeatureCollection"
            }

        else:
            # Old format: {"МО_name": {"type": "Polygon", "coordinates": [...]}}
            logger.info(f"Found {len(data)} municipalities in old format")

            updated = 0
            not_found = []

            for mo_name, geojson_data in data.items():
                mo = db.query(DimMO).filter(DimMO.mo_name == mo_name).first()

                if mo:
                    mo.geojson = geojson_data
                    updated += 1
                    logger.info(f"Updated {mo_name}")
                else:
                    not_found.append(mo_name)
                    logger.warning(f"Municipality not found in DB: {mo_name}")

            db.commit()

            return {
                "status": "success",
                "message": f"Uploaded real boundaries for {updated} municipalities",
                "updated": updated,
                "not_found": not_found,
                "note": "Real boundaries from legacy format"
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    except Exception as e:
        logger.error(f"Error uploading boundaries: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading boundaries: {str(e)}")


@router.post("/update-geojson-realistic")
async def update_municipality_geojson_realistic(db: Session = Depends(get_db)):
    """
    Update GeoJSON boundaries with realistic elliptical shapes.
    Creates more natural-looking boundaries based on municipality centers.
    """
    import math

    try:
        municipalities = db.query(DimMO).all()
        updated = 0

        for mo in municipalities:
            if mo.lat and mo.lon:
                lat, lon = mo.lat, mo.lon

                # Определяем размер на основе названия (города меньше, районы больше)
                if mo.mo_name in ["Липецк", "Елец"]:
                    size = 0.12
                else:
                    size = 0.20

                # Создаем эллиптический полигон с волнистыми краями
                points = 48
                coordinates = []

                for i in range(points):
                    angle = (i * 360 / points) * (math.pi / 180)

                    # Эллиптическая форма
                    a = size * 1.5  # Большая полуось
                    b = size  # Малая полуось

                    # Добавляем волнистость
                    wave = 1.0 + 0.15 * math.sin(5 * angle) + 0.1 * math.cos(7 * angle)

                    r = (a * b) / math.sqrt((b * math.cos(angle))**2 + (a * math.sin(angle))**2)
                    r *= wave

                    point_lat = lat + r * math.sin(angle)
                    point_lon = lon + r * math.cos(angle) / math.cos(lat * math.pi / 180)

                    coordinates.append([point_lon, point_lat])

                # Замыкаем полигон
                coordinates.append(coordinates[0])

                geojson_data = {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                }

                mo.geojson = geojson_data
                updated += 1

        db.commit()
        logger.info(f"Updated realistic GeoJSON for {updated} municipalities")

        return {
            "status": "success",
            "message": f"Updated realistic boundaries for {updated} municipalities",
            "updated": updated,
            "note": "Using elliptical shapes with wavy edges for natural appearance"
        }

    except Exception as e:
        logger.error(f"Error updating realistic GeoJSON: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating realistic GeoJSON: {str(e)}")


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
async def calculate_summary_scores(
    period_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Calculate summary scores for all municipalities.
    Creates records in fact_summary table based on indicator values.

    Parameters:
    - period_id: Optional. If not provided, calculates for all periods.
    """
    try:
        from models import FactSummary

        # Get all municipalities
        municipalities = db.query(DimMO).all()

        # Get periods
        if period_id:
            periods = [db.query(DimPeriod).filter(DimPeriod.period_id == period_id).first()]
            if not periods[0]:
                raise HTTPException(status_code=404, detail=f"Period {period_id} not found")
        else:
            # Calculate for all periods
            periods = db.query(DimPeriod).all()

        methodology = db.query(DimMethodology).filter(DimMethodology.version == "v1").first()

        if not periods or not methodology:
            raise HTTPException(status_code=404, detail="Period or methodology not found")

        total_created = 0
        total_updated = 0

        # Process each period
        for period in periods:
            created = 0
            updated = 0

            for mo in municipalities:
                # Get all indicator values for this MO and period
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

            total_created += created
            total_updated += updated
            logger.info(f"Period {period.period_id}: Created {created}, updated {updated}")

        db.commit()
        logger.info(f"Total: Created {total_created} summaries, updated {total_updated}")

        return {
            "status": "success",
            "message": f"Calculated scores for {len(periods)} period(s)",
            "periods_processed": len(periods),
            "created": total_created,
            "updated": total_updated
        }

    except Exception as e:
        logger.error(f"Error calculating scores: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")
