"""
Database migrations - Executed automatically on application startup
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from database import SessionLocal, engine

logger = logging.getLogger(__name__)


def apply_leader_name_column_migration():
    """
    Migration: Add leader_name column to dim_mo and populate with real data
    This is executed automatically on app startup
    """
    try:
        session = SessionLocal()

        # Check if leader_name column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('dim_mo')]

        if 'leader_name' not in columns:
            logger.info("🔄 Running migration: Adding leader_name column to dim_mo...")

            # Create column
            session.execute(text("""
                ALTER TABLE dim_mo ADD COLUMN leader_name VARCHAR(255)
            """))
            logger.info("✓ Column leader_name created")

            # Populate with real data
            leader_data = [
                ('Липецк', 'Ченцов Р.И.', '%Липецк%', 'NOT LIKE', '%Липецкий%'),
                ('Елец', 'Жабин В.П.', '%Елец%', 'NOT LIKE', '%Елецкий%'),
                ('Воловский', 'Щеглов С.С.', '%Воловский%', 'LIKE', '%'),
                ('Грязянский', 'Рощупкин В.Т.', '%Грязянский%', 'LIKE', '%'),
                ('Данковский', 'Фалеев В.И.', '%Данковский%', 'LIKE', '%'),
                ('Добринский', 'Пасынков А.Н.', '%Добринский%', 'LIKE', '%'),
                ('Добровский', 'Попов А.А.', '%Добровский%', 'LIKE', '%'),
                ('Долгоруковский', 'Тимохин А.Н.', '%Долгоруковский%', 'LIKE', '%'),
                ('Елецкий', 'Семенихин О.Н.', '%Елецкий%', 'LIKE', '%'),
                ('Задонский', 'Щедров А.И.', '%Задонский%', 'LIKE', '%'),
                ('Измалковский', 'Иванников В.Ю.', '%Измалковский%', 'LIKE', '%'),
                ('Краснинский', 'Поляков С.О.', '%Краснинский%', 'LIKE', '%'),
                ('Лебедянский', 'Телков А.М.', '%Лебедянский%', 'LIKE', '%'),
                ('Лев-Толстовский', 'Шабанов К.Ю.', '%Лев-Толстовский%', 'LIKE', '%'),
                ('Липецкий', 'Тодуа Д.В.', '%Липецкий%', 'LIKE', '%'),
                ('Становлянский', 'Семянников Д.Ю.', '%Становлянский%', 'LIKE', '%'),
                ('Тербунский', 'Черников Н.Е.', '%Тербунский%', 'LIKE', '%'),
                ('Усманский', 'Мазо В.М.', '%Усманский%', 'LIKE', '%'),
                ('Хлевенский', 'Плотников А.И.', '%Хлевенский%', 'LIKE', '%'),
                ('Чаплыгинский', 'Сазонов Ю.А.', '%Чаплыгинский%', 'LIKE', '%'),
            ]

            # Update each leader
            for mo_name, leader_name, pattern, operator, exclude_pattern in leader_data:
                if operator == 'NOT LIKE':
                    sql = f"UPDATE dim_mo SET leader_name = :leader WHERE mo_name ILIKE :pattern AND mo_name NOT ILIKE :exclude"
                    session.execute(text(sql), {
                        'leader': leader_name,
                        'pattern': pattern,
                        'exclude': exclude_pattern
                    })
                else:
                    sql = f"UPDATE dim_mo SET leader_name = :leader WHERE mo_name ILIKE :pattern"
                    session.execute(text(sql), {
                        'leader': leader_name,
                        'pattern': pattern
                    })

            session.commit()

            # Verify
            result = session.execute(text("SELECT COUNT(*) FROM dim_mo WHERE leader_name IS NOT NULL"))
            count = result.scalar()
            logger.info(f"✓ Populated {count} leader names")

        else:
            logger.info("✓ Column leader_name already exists, skipping migration")

        session.close()

    except Exception as e:
        logger.error(f"✗ Migration failed: {str(e)}")
        logger.info("⚠ App will continue, but leader_name column may not exist")
        try:
            session.close()
        except:
            pass


def apply_criteria_blocks_migration():
    """
    Migration: Create dim_criteria_block table and add block_id columns to dim_indicator
    """
    try:
        session = SessionLocal()

        # Check if dim_criteria_block table exists
        inspector = inspect(engine)
        tables = [table.name for table in inspector.get_table_names()]

        # Create dim_criteria_block table if not exists
        if 'dim_criteria_block' not in tables:
            logger.info("🔄 Running migration: Creating dim_criteria_block table...")

            session.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_criteria_block (
                    block_id SERIAL PRIMARY KEY,
                    block_name VARCHAR(255) NOT NULL UNIQUE,
                    block_order INTEGER,
                    description TEXT,
                    is_visible BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            logger.info("✓ dim_criteria_block table created")

        # Add missing columns to dim_indicator
        inspector = inspect(engine)  # Refresh inspector
        indicator_columns = [col['name'] for col in inspector.get_columns('dim_indicator')]

        if 'block_id' not in indicator_columns:
            logger.info("🔄 Running migration: Adding block_id to dim_indicator...")
            session.execute(text("""
                ALTER TABLE dim_indicator
                ADD COLUMN block_id INTEGER REFERENCES dim_criteria_block(block_id)
            """))
            session.commit()
            logger.info("✓ block_id column added to dim_indicator")

        if 'criteria_order' not in indicator_columns:
            logger.info("🔄 Running migration: Adding criteria_order to dim_indicator...")
            session.execute(text("""
                ALTER TABLE dim_indicator
                ADD COLUMN criteria_order INTEGER
            """))
            session.commit()
            logger.info("✓ criteria_order column added to dim_indicator")

        # Insert criteria blocks if they don't exist
        logger.info("🔄 Populating criteria blocks...")
        blocks = [
            ('Политический менеджмент', 1, 'Критерии политического управления МО'),
            ('Забота и внимание', 2, 'Критерии социальной политики и вовлеченности'),
            ('Развитие кадрового и проектного потенциала МО', 3, 'Критерии развития кадров и проектов'),
            ('Штрафные критерии', 4, 'Критерии с отрицательными баллами'),
        ]

        for block_name, block_order, description in blocks:
            session.execute(text("""
                INSERT INTO dim_criteria_block (block_name, block_order, description, is_visible)
                VALUES (:name, :order, :desc, true)
                ON CONFLICT (block_name) DO NOTHING
            """), {
                'name': block_name,
                'order': block_order,
                'desc': description
            })

        session.commit()
        logger.info("✓ Criteria blocks populated")
        session.close()

    except Exception as e:
        logger.error(f"✗ Criteria blocks migration failed: {str(e)}")
        logger.info("⚠ App will continue, but criteria blocks may not be set up")
        try:
            session.rollback()
            session.close()
        except:
            pass


def run_all_migrations():
    """Run all database migrations on startup"""
    logger.info("=" * 80)
    logger.info("🔧 Running database migrations...")
    logger.info("=" * 80)

    apply_leader_name_column_migration()
    apply_criteria_blocks_migration()

    logger.info("=" * 80)
    logger.info("✓ All migrations completed")
    logger.info("=" * 80)
