#!/usr/bin/env python3
"""
ETL скрипт для загрузки данных в PostgreSQL НА АМВЕРА СЕРВЕРЕ.

Этот скрипт специально предназначен для запуска внутри контейнера Backend на Amvera,
где БД доступна через локальное подключение к сервису 'postgres'.

Использование:
  # В контейнере Amvera Backend:
  $ python etl/load_to_db_amvera.py
"""

import json
import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URL для подключения ИЗ КОНТЕЙНЕРА
# Когда запускаете в контейнере Amvera, используйте:
# - host: postgres (название сервиса в docker-compose)
# - password: Qwerty12345 (пароль reyting_user)

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://reyting_user:Qwerty12345@postgres:5432/reytingdb'
)

# Для тестирования локально (если нужно):
# DATABASE_URL = 'postgresql://dashboard_user:dashboard_password@localhost:5432/dashboard_db'

# Папка с извлеченными данными
DATA_FOLDER = Path(__file__).parent.parent
EXTRACTED_DATA_FILE = DATA_FOLDER / "extracted_data.json"

def get_db_engine():
    """Создает подключение к БД."""
    try:
        logger.info(f"📡 Подключаюсь к БД: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Успешно подключились к БД")
        return engine
    except Exception as e:
        logger.error(f"✗ Ошибка подключения к БД: {e}")
        logger.error(f"  Убедитесь что:")
        logger.error(f"  1. БД инициализирована (database_schema.sql выполнена)")
        logger.error(f"  2. Пароль правильный: Qwerty12345")
        logger.error(f"  3. Если локально - используйте localhost вместо postgres")
        sys.exit(1)

def get_municipality_id(session, mo_name):
    """Получает ID муниципалитета по названию."""
    try:
        result = session.execute(
            text("SELECT mo_id FROM dim_mo WHERE mo_name ILIKE :name LIMIT 1"),
            {"name": f"%{mo_name}%"}
        ).fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.debug(f"Ошибка при поиске МО '{mo_name}': {e}")
        return None

def get_or_create_period(session, period_desc='2024-Q4'):
    """Получает или создает период."""
    try:
        result = session.execute(
            text("SELECT period_id FROM dim_period WHERE description = :desc LIMIT 1"),
            {"desc": period_desc}
        ).fetchone()

        if result:
            return result[0]

        logger.info(f"  Создаю новый период: {period_desc}")
        session.execute(
            text("""
                INSERT INTO dim_period (period_type, date_from, date_to, description)
                VALUES (:type, '2024-01-01', '2024-12-31', :desc)
            """),
            {"type": "year", "desc": period_desc}
        )
        session.commit()

        result = session.execute(
            text("SELECT period_id FROM dim_period WHERE description = :desc"),
            {"desc": period_desc}
        ).fetchone()

        return result[0] if result else None

    except Exception as e:
        logger.debug(f"Ошибка при работе с периодом: {e}")
        return None

def get_or_create_indicator(session, indicator_code, indicator_name):
    """Получает или создает индикатор."""
    try:
        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE code = :code LIMIT 1"),
            {"code": indicator_code}
        ).fetchone()

        if result:
            return result[0]

        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE name ILIKE :name LIMIT 1"),
            {"name": f"%{indicator_name}%"}
        ).fetchone()

        if result:
            return result[0]

        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE code = 'OTHER' LIMIT 1")
        ).fetchone()

        return result[0] if result else None

    except Exception as e:
        logger.debug(f"Ошибка при работе с индикатором: {e}")
        return None

def load_data_to_db(data, engine, session):
    """Загружает данные в БД."""
    logger.info("\n" + "=" * 70)
    logger.info("📊 ЗАГРУЗКА ДАННЫХ В БД")
    logger.info("=" * 70)

    period_id = get_or_create_period(session)
    if not period_id:
        logger.error("✗ Не удалось получить или создать период")
        return 0

    logger.info(f"✓ Используем период: {period_id}\n")

    loaded_count = 0
    skipped_count = 0
    error_count = 0

    for idx, record in enumerate(data):
        try:
            if (idx + 1) % 1000 == 0:
                logger.info(f"  ✓ Обработано {idx + 1}/{len(data)} записей...")

            mo_name = record.get('mo_name', '').strip()
            value_raw = record.get('value_raw')
            indicator_code = record.get('indicator_code', 'OTHER')
            category = record.get('category', '')

            if not mo_name or value_raw is None:
                skipped_count += 1
                continue

            mo_id = get_municipality_id(session, mo_name)
            if not mo_id:
                skipped_count += 1
                continue

            ind_id = get_or_create_indicator(session, indicator_code, category)
            if not ind_id:
                skipped_count += 1
                continue

            value_norm = float(value_raw)
            if 0 <= value_norm <= 1:
                value_norm = value_norm * 100
            else:
                value_norm = min(100, max(0, value_norm))

            if value_norm >= 75:
                score = 10
            elif value_norm >= 50:
                score = 5
            else:
                score = 0

            try:
                session.execute(
                    text("""
                        INSERT INTO fact_indicator
                        (mo_id, period_id, ind_id, value_raw, value_norm, score)
                        VALUES (:mo_id, :period_id, :ind_id, :value_raw, :value_norm, :score)
                        ON CONFLICT (mo_id, period_id, ind_id) DO UPDATE SET
                            value_raw = EXCLUDED.value_raw,
                            value_norm = EXCLUDED.value_norm,
                            score = EXCLUDED.score
                    """),
                    {
                        "mo_id": mo_id,
                        "period_id": period_id,
                        "ind_id": ind_id,
                        "value_raw": float(value_raw),
                        "value_norm": float(value_norm),
                        "score": int(score)
                    }
                )
                loaded_count += 1

                if loaded_count % 500 == 0:
                    session.commit()

            except Exception as insert_error:
                logger.debug(f"  Ошибка при вставке: {insert_error}")
                error_count += 1
                continue

        except Exception as e:
            logger.debug(f"  Ошибка обработки записи {idx}: {e}")
            error_count += 1
            continue

    session.commit()

    logger.info("=" * 70)
    logger.info(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА")
    logger.info(f"   Загружено записей: {loaded_count}")
    logger.info(f"   Пропущено: {skipped_count}")
    logger.info(f"   Ошибок: {error_count}")
    logger.info(f"   Всего обработано: {len(data)}")
    logger.info("=" * 70)

    return loaded_count

def verify_data(session):
    """Проверяет загруженные данные."""
    logger.info("\n" + "=" * 70)
    logger.info("🔍 ПРОВЕРКА ЗАГРУЖЕННЫХ ДАННЫХ")
    logger.info("=" * 70)

    try:
        result = session.execute(
            text("SELECT COUNT(*) FROM fact_indicator")
        ).fetchone()
        total = result[0] if result else 0
        logger.info(f"✓ Всего записей в fact_indicator: {total}")

        result = session.execute(
            text("""
                SELECT mo.mo_name, COUNT(*) as count
                FROM fact_indicator fi
                JOIN dim_mo mo ON fi.mo_id = mo.mo_id
                GROUP BY mo.mo_id, mo.mo_name
                ORDER BY count DESC
                LIMIT 10
            """)
        ).fetchall()

        logger.info(f"✓ Топ 10 МО по количеству записей:")
        for mo_name, count in result:
            logger.info(f"   {mo_name}: {count}")

        result = session.execute(
            text("""
                SELECT ind.name, COUNT(*) as count
                FROM fact_indicator fi
                JOIN dim_indicator ind ON fi.ind_id = ind.ind_id
                GROUP BY fi.ind_id, ind.name
                ORDER BY count DESC
                LIMIT 5
            """)
        ).fetchall()

        logger.info(f"✓ Топ 5 индикаторов по количеству записей:")
        for ind_name, count in result:
            logger.info(f"   {ind_name}: {count}")

    except Exception as e:
        logger.error(f"✗ Ошибка при проверке: {e}")

    logger.info("=" * 70)

def main():
    """Главная функция."""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 ЗАГРУЗКА ДАННЫХ НА AMVERA")
    logger.info("=" * 70)
    logger.info(f"📁 Файл данных: {EXTRACTED_DATA_FILE}")
    logger.info(f"🗄️  БД: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    logger.info("=" * 70)

    if not EXTRACTED_DATA_FILE.exists():
        logger.error(f"✗ Файл не найден: {EXTRACTED_DATA_FILE}")
        logger.info("  Убедитесь что extracted_data.json находится в корне проекта")
        logger.info("  Сначала запустите: python etl/load_assessment_data_v2.py")
        sys.exit(1)

    engine = get_db_engine()
    session = Session(engine)

    try:
        logger.info(f"\n📖 Загружаю данные из: {EXTRACTED_DATA_FILE.name}")

        with open(EXTRACTED_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"✓ Загружено {len(data)} записей из JSON\n")

        loaded = load_data_to_db(data, engine, session)

        verify_data(session)

        if loaded > 0:
            logger.info("\n✅ УСПЕШНО ЗАГРУЖЕНО!")
            logger.info(f"   Данные доступны на https://reyting.amvera.ru")
        else:
            logger.warning("\n⚠ Не загружено ни одной записи")

    except Exception as e:
        logger.error(f"✗ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()

    logger.info("\n" + "=" * 70)
    logger.info("✅ Завершено")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
