#!/usr/bin/env python3
"""
ETL скрипт для загрузки извлеченных данных в PostgreSQL на Amvera.
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

# Database URL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://reyting_user:password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb'
)

# Папка с данными
DATA_FOLDER = Path(__file__).parent.parent.parent
EXTRACTED_DATA_FILE = DATA_FOLDER / "extracted_data.json"

def get_db_engine():
    """Создает подключение к БД."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Успешно подключились к БД")
        return engine
    except Exception as e:
        logger.error(f"✗ Ошибка подключения к БД: {e}")
        logger.error(f"  DATABASE_URL: {DATABASE_URL}")
        sys.exit(1)

def load_extracted_data(filepath):
    """Загружает извлеченные данные из JSON."""
    logger.info(f"📖 Загружаю данные из: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"✓ Загружено {len(data)} записей из JSON")
        return data
    except Exception as e:
        logger.error(f"✗ Ошибка при чтении файла: {e}")
        return []

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
        # Проверяем есть ли уже такой период
        result = session.execute(
            text("SELECT period_id FROM dim_period WHERE description = :desc LIMIT 1"),
            {"desc": period_desc}
        ).fetchone()

        if result:
            return result[0]

        # Создаем новый период
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
        # Проверяем есть ли индикатор с таким кодом
        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE code = :code LIMIT 1"),
            {"code": indicator_code}
        ).fetchone()

        if result:
            return result[0]

        # Пытаемся найти похожий индикатор по названию
        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE name ILIKE :name LIMIT 1"),
            {"name": f"%{indicator_name}%"}
        ).fetchone()

        if result:
            return result[0]

        # Если не найден, используем индикатор "OTHER" или создаем новый
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

    logger.info(f"✓ Используем период: {period_id}")

    loaded_count = 0
    skipped_count = 0
    error_count = 0

    # Обрабатываем данные
    for idx, record in enumerate(data):
        try:
            if (idx + 1) % 1000 == 0:
                logger.info(f"  Обработано {idx + 1}/{len(data)} записей...")

            # Получаем нужные данные
            mo_name = record.get('mo_name', '').strip()
            value_raw = record.get('value_raw')
            indicator_code = record.get('indicator_code', 'OTHER')
            category = record.get('category', '')

            # Пропускаем если нет МО или значения
            if not mo_name or value_raw is None:
                skipped_count += 1
                continue

            # Получаем ID МО
            mo_id = get_municipality_id(session, mo_name)
            if not mo_id:
                logger.debug(f"  ⚠ МО не найдена: '{mo_name}'")
                skipped_count += 1
                continue

            # Получаем ID индикатора
            ind_id = get_or_create_indicator(session, indicator_code, category)
            if not ind_id:
                logger.debug(f"  ⚠ Индикатор не найден: '{indicator_code}'")
                skipped_count += 1
                continue

            # Нормализуем значение
            value_norm = float(value_raw)
            if 0 <= value_norm <= 1:
                value_norm = value_norm * 100
            else:
                value_norm = min(100, max(0, value_norm))

            # Вычисляем score
            if value_norm >= 75:
                score = 10
            elif value_norm >= 50:
                score = 5
            else:
                score = 0

            # Вставляем в БД
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

                # Коммитим каждые 500 записей
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

    # Финальный коммит
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
        # Количество записей
        result = session.execute(
            text("SELECT COUNT(*) FROM fact_indicator")
        ).fetchone()
        total = result[0] if result else 0
        logger.info(f"✓ Всего записей в fact_indicator: {total}")

        # По МО
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

        # По индикаторам
        result = session.execute(
            text("""
                SELECT ind.name, COUNT(*) as count
                FROM fact_indicator fi
                JOIN dim_indicator ind ON fi.ind_id = ind.ind_id
                GROUP BY fi.ind_id, ind.name
                ORDER BY count DESC
                LIMIT 10
            """)
        ).fetchall()

        logger.info(f"✓ Топ 10 индикаторов по количеству записей:")
        for ind_name, count in result:
            logger.info(f"   {ind_name}: {count}")

    except Exception as e:
        logger.error(f"✗ Ошибка при проверке: {e}")

    logger.info("=" * 70)

def main():
    """Главная функция."""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 ЗАГРУЗКА ДАННЫХ В POSTGRESQL НА AMVERA")
    logger.info("=" * 70)
    logger.info(f"📁 Файл данных: {EXTRACTED_DATA_FILE}")
    logger.info(f"🗄️  БД: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    logger.info("=" * 70)

    # Проверяем что файл существует
    if not EXTRACTED_DATA_FILE.exists():
        logger.error(f"✗ Файл не найден: {EXTRACTED_DATA_FILE}")
        logger.info("  Сначала запустите: python etl/load_assessment_data_v2.py")
        sys.exit(1)

    # Подключаемся к БД
    engine = get_db_engine()
    session = Session(engine)

    try:
        # Загружаем данные из JSON
        data = load_extracted_data(EXTRACTED_DATA_FILE)
        if not data:
            logger.error("✗ Не удалось загрузить данные")
            sys.exit(1)

        # Загружаем в БД
        loaded = load_data_to_db(data, engine, session)

        # Проверяем результаты
        verify_data(session)

        if loaded > 0:
            logger.info("\n✅ УСПЕШНО ЗАГРУЖЕНО!")
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
