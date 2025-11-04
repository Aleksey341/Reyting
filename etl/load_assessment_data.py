#!/usr/bin/env python3
"""
ETL скрипт для загрузки данных оценки эффективности руководителей в БД.

Загружает CSV файлы из папки data_extract в PostgreSQL на Amvera.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URL - можно заменить на переменную окружения
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://reyting_user:password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb'
)

# Папка с данными
DATA_FOLDER = Path(__file__).parent.parent.parent / "data_extract"

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
        sys.exit(1)

def get_municipality_id(session, mo_name):
    """Получает ID муниципалитета по названию."""
    result = session.execute(
        text("SELECT mo_id FROM dim_mo WHERE mo_name ILIKE :name"),
        {"name": f"%{mo_name}%"}
    ).fetchone()
    return result[0] if result else None

def get_indicator_id(session, indicator_name, block_name='Оценка поддержки'):
    """Получает ID индикатора по названию."""
    result = session.execute(
        text("""
            SELECT ind_id FROM dim_indicator
            WHERE name ILIKE :name OR code ILIKE :code
            ORDER BY ind_id LIMIT 1
        """),
        {"name": f"%{indicator_name}%", "code": f"%{indicator_name}%"}
    ).fetchone()

    if not result:
        # Если не найден, создаем новый индикатор
        logger.warning(f"⚠ Индикатор '{indicator_name}' не найден, используем 'Другой'")
        result = session.execute(
            text("SELECT ind_id FROM dim_indicator WHERE code = 'OTHER' LIMIT 1")
        ).fetchone()

    return result[0] if result else None

def get_or_create_period(session, period_name='2024-Q4'):
    """Получает или создает период."""
    result = session.execute(
        text("SELECT period_id FROM dim_period WHERE description = :desc LIMIT 1"),
        {"desc": period_name}
    ).fetchone()

    if result:
        return result[0]

    # Создаем новый период
    session.execute(
        text("""
            INSERT INTO dim_period (period_type, date_from, date_to, description)
            VALUES (:type, '2024-01-01', '2024-12-31', :desc)
            RETURNING period_id
        """),
        {"type": "year", "desc": period_name}
    )
    session.commit()

    result = session.execute(
        text("SELECT period_id FROM dim_period WHERE description = :desc"),
        {"desc": period_name}
    ).fetchone()

    return result[0]

def parse_value(value):
    """Преобразует значение в число или None."""
    if value is None or (isinstance(value, str) and value.strip() == ''):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Обработка "Да"/"Нет" как 1/0
        if value.lower() in ['да', 'yes', 'true', '1']:
            return 1.0
        if value.lower() in ['нет', 'no', 'false', '0']:
            return 0.0

        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return None

    return None

def load_csv_file(filepath, engine, session):
    """Загружает данные из одного CSV файла."""
    logger.info(f"\n📊 Загружаю файл: {filepath.name}")

    try:
        # Читаем CSV
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        logger.info(f"   Загружено {len(df)} строк")

        # Если файл пустой, пропускаем
        if df.empty:
            logger.warning(f"   ⚠ Файл пуст, пропускаю")
            return 0

        # Стандартные колонки которые есть во всех файлах
        required_cols = ['Муниципалитет', 'Глава МО', 'Лист']

        # Проверяем наличие нужных колонок
        if 'Муниципалитет' not in df.columns:
            logger.warning(f"   ⚠ Нет колонки 'Муниципалитет', пропускаю")
            return 0

        loaded_count = 0

        # Для каждой строки в CSV
        for idx, row in df.iterrows():
            try:
                mo_name = str(row.get('Муниципалитет', '')).strip()
                indicator_name = str(row.get('Лист', '')).strip()

                if not mo_name or mo_name == 'nan' or mo_name == '':
                    continue

                # Получаем ID муниципалитета
                mo_id = get_municipality_id(session, mo_name)
                if not mo_id:
                    logger.debug(f"   ⚠ МО не найдена: '{mo_name}'")
                    continue

                # Получаем ID индикатора (если есть)
                indicator_name = indicator_name if indicator_name and indicator_name != 'nan' else 'Общая оценка'
                ind_id = get_indicator_id(session, indicator_name)
                if not ind_id:
                    continue

                # Получаем период
                period_id = get_or_create_period(session)

                # Собираем все числовые значения из строки
                for col in df.columns:
                    if col in required_cols:
                        continue

                    value = parse_value(row.get(col))
                    if value is None:
                        continue

                    # Нормализуем значение (в диапазон 0-100)
                    if 0 <= value <= 1:
                        value_norm = value * 100
                    else:
                        value_norm = min(100, max(0, value))

                    # Вычисляем score (в зависимости от значения)
                    if value_norm >= 75:
                        score = 10
                    elif value_norm >= 50:
                        score = 5
                    else:
                        score = 0

                    # Вставляем в fact_indicator
                    try:
                        session.execute(
                            text("""
                                INSERT INTO fact_indicator
                                (mo_id, period_id, ind_id, value_raw, value_norm, score)
                                VALUES (:mo_id, :period_id, :ind_id, :value_raw, :value_norm, :score)
                                ON CONFLICT DO NOTHING
                            """),
                            {
                                "mo_id": mo_id,
                                "period_id": period_id,
                                "ind_id": ind_id,
                                "value_raw": float(value),
                                "value_norm": float(value_norm),
                                "score": int(score)
                            }
                        )
                        loaded_count += 1
                    except Exception as e:
                        logger.debug(f"   Ошибка при вставке: {e}")
                        continue

            except Exception as e:
                logger.debug(f"   Ошибка при обработке строки {idx}: {e}")
                continue

        session.commit()
        logger.info(f"   ✓ Загружено {loaded_count} записей")
        return loaded_count

    except Exception as e:
        logger.error(f"   ✗ Ошибка при загрузке файла: {e}")
        return 0

def load_all_data(data_folder):
    """Загружает все CSV файлы из папки."""
    engine = get_db_engine()
    session = Session(engine)

    try:
        # Проверяем что папка существует
        if not data_folder.exists():
            logger.error(f"✗ Папка не найдена: {data_folder}")
            return

        # Находим все CSV файлы
        csv_files = sorted(data_folder.glob("*.csv"))

        if not csv_files:
            logger.error(f"✗ CSV файлы не найдены в папке: {data_folder}")
            return

        logger.info(f"📁 Найдено {len(csv_files)} CSV файлов")

        total_loaded = 0

        # Загружаем каждый файл
        for csv_file in csv_files:
            count = load_csv_file(csv_file, engine, session)
            total_loaded += count

        logger.info(f"\n✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        logger.info(f"   Всего загружено записей: {total_loaded}")

    except Exception as e:
        logger.error(f"✗ Критическая ошибка: {e}")
    finally:
        session.close()
        engine.dispose()

def main():
    """Главная функция."""
    logger.info("=" * 70)
    logger.info("📊 ЗАГРУЗКА ДАННЫХ ОЦЕНКИ ЭФФЕКТИВНОСТИ РУКОВОДИТЕЛЕЙ")
    logger.info("=" * 70)
    logger.info(f"📁 Папка с данными: {DATA_FOLDER}")
    logger.info(f"🗄️  БД: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    logger.info("=" * 70)

    load_all_data(DATA_FOLDER)

    logger.info("=" * 70)
    logger.info("✅ Завершено")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
