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


def apply_dim_indicator_columns_migration():
    """
    Migration: Fix dim_indicator table to include block_id and criteria_order columns
    Recreates table to ensure all columns exist
    """
    try:
        session = SessionLocal()

        # Check if block_id column exists
        inspector = inspect(engine)
        indicator_columns = [col['name'] for col in inspector.get_columns('dim_indicator')]

        if 'block_id' not in indicator_columns:
            logger.info("🔄 Running migration: Fixing dim_indicator table structure...")

            # Drop foreign key constraints
            session.execute(text("ALTER TABLE fact_indicator DROP CONSTRAINT IF EXISTS fact_indicator_ind_id_fkey"))
            session.execute(text("ALTER TABLE map_scale DROP CONSTRAINT IF EXISTS map_scale_ind_id_fkey"))
            session.commit()

            # Create backup
            session.execute(text("CREATE TABLE dim_indicator_backup AS SELECT * FROM dim_indicator"))
            session.commit()
            logger.info("✓ Created backup of dim_indicator")

            # Drop old table
            session.execute(text("DROP TABLE IF EXISTS dim_indicator CASCADE"))
            session.commit()
            logger.info("✓ Dropped old dim_indicator table")

            # Create new table with all columns
            session.execute(text("""
                CREATE TABLE dim_indicator (
                    ind_id SERIAL PRIMARY KEY,
                    code VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    block VARCHAR(100),
                    block_id INTEGER,
                    criteria_order INTEGER,
                    description TEXT,
                    unit VARCHAR(50),
                    is_public BOOLEAN DEFAULT true,
                    owner_org VARCHAR(100),
                    weight FLOAT,
                    min_value FLOAT,
                    max_value FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            logger.info("✓ Created new dim_indicator table with all columns")

            # Restore data from backup
            session.execute(text("""
                INSERT INTO dim_indicator (ind_id, code, name, block, description, unit, is_public, owner_org, weight, min_value, max_value, created_at, updated_at)
                SELECT ind_id, code, name, block, description, unit, is_public, owner_org, weight, min_value, max_value, created_at, updated_at
                FROM dim_indicator_backup
            """))
            session.commit()
            logger.info("✓ Restored data from backup")

            # Re-add foreign keys
            session.execute(text("""
                ALTER TABLE fact_indicator ADD CONSTRAINT fact_indicator_ind_id_fkey
                FOREIGN KEY (ind_id) REFERENCES dim_indicator(ind_id)
            """))
            session.execute(text("""
                ALTER TABLE map_scale ADD CONSTRAINT map_scale_ind_id_fkey
                FOREIGN KEY (ind_id) REFERENCES dim_indicator(ind_id)
            """))
            session.commit()
            logger.info("✓ Re-added foreign key constraints")

            # Drop backup
            session.execute(text("DROP TABLE dim_indicator_backup"))
            session.commit()
            logger.info("✓ Cleaned up backup table")

            # Verify
            result = session.execute(text("SELECT COUNT(*) FROM dim_indicator"))
            count = result.scalar()
            logger.info(f"✓ dim_indicator has {count} rows")

        else:
            logger.info("✓ Column block_id already exists in dim_indicator, skipping migration")

        session.close()

    except Exception as e:
        logger.error(f"✗ dim_indicator columns migration failed: {str(e)}")
        logger.info("⚠ App will continue, but some features may not work")
        try:
            session.rollback()
            session.close()
        except:
            pass


def apply_criteria_blocks_migration():
    """
    Migration: Create dim_criteria_block table and populate with block structure
    """
    try:
        session = SessionLocal()

        # Check if dim_criteria_block table exists
        inspector = inspect(engine)
        tables = [table.name for table in inspector.get_table_names()]

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

    # Order matters! Fix table structure first, then add data
    apply_dim_indicator_columns_migration()  # Fix dim_indicator table structure
    apply_leader_name_column_migration()      # Add leader_name column and data
    apply_criteria_blocks_migration()         # Create criteria blocks

    logger.info("=" * 80)
    logger.info("✓ All migrations completed")
    logger.info("=" * 80)
