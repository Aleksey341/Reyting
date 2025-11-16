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


def fix_fact_indicator_scores():
    """
    Migration: Fix NULL score values in fact_indicator
    Fill score from value_raw if score is NULL
    """
    try:
        session = SessionLocal()

        # Check if there are any NULL scores
        null_score_count = session.execute(
            text("SELECT COUNT(*) FROM fact_indicator WHERE score IS NULL")
        ).scalar()

        if null_score_count > 0:
            logger.info(f"🔄 Running migration: Fixing {null_score_count} NULL scores in fact_indicator...")

            # Update NULL scores from value_raw
            session.execute(text("""
                UPDATE fact_indicator
                SET score = value_raw
                WHERE score IS NULL AND value_raw IS NOT NULL
            """))

            # For records where both are NULL, set to 0
            session.execute(text("""
                UPDATE fact_indicator
                SET score = 0
                WHERE score IS NULL
            """))

            session.commit()

            # Verify
            result = session.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN score IS NOT NULL THEN 1 END) as with_score,
                       COUNT(CASE WHEN score IS NULL THEN 1 END) as without_score
                FROM fact_indicator
            """))
            row = result.fetchone()
            logger.info(f"✓ Fact indicator scores fixed: total={row[0]}, with_score={row[1]}, without_score={row[2]}")

        else:
            logger.info("✓ No NULL scores found in fact_indicator, skipping migration")

        session.close()

    except Exception as e:
        logger.error(f"✗ Fact indicator scores migration failed: {str(e)}")
        try:
            session.rollback()
            session.close()
        except:
            pass


def ensure_proper_indicator_codes():
    """
    Migration: Ensure dim_indicator has proper codes (pm_01, ca_01, dev_01, pen_01)
    Delete indicators created by CSV import that don't have proper codes
    """
    try:
        session = SessionLocal()

        # Check how many indicators don't have proper codes
        bad_indicators = session.execute(text("""
            SELECT COUNT(*) FROM dim_indicator
            WHERE code NOT LIKE 'pm_%'
              AND code NOT LIKE 'ca_%'
              AND code NOT LIKE 'dev_%'
              AND code NOT LIKE 'pen_%'
        """)).scalar()

        if bad_indicators > 0:
            logger.info(f"🔄 Running migration: Removing {bad_indicators} indicators with improper codes...")

            # Delete foreign key constraints
            session.execute(text("""
                ALTER TABLE fact_indicator DROP CONSTRAINT IF EXISTS fact_indicator_ind_id_fkey
            """))
            session.execute(text("""
                ALTER TABLE map_scale DROP CONSTRAINT IF EXISTS map_scale_ind_id_fkey
            """))

            # Delete bad indicators
            session.execute(text("""
                DELETE FROM dim_indicator
                WHERE code NOT LIKE 'pm_%'
                  AND code NOT LIKE 'ca_%'
                  AND code NOT LIKE 'dev_%'
                  AND code NOT LIKE 'pen_%'
            """))

            session.commit()
            logger.info(f"✓ Removed {bad_indicators} indicators with improper codes")

            # Now insert proper ones
            logger.info("🔄 Inserting proper indicators with codes...")
            proper_indicators = [
                ('pm_01', 'Оценка поддержки руководства области', 'Политический менеджмент'),
                ('pm_02', 'Выполнение задач АГП', 'Политический менеджмент'),
                ('pm_03', 'Позиционирование главы МО', 'Политический менеджмент'),
                ('pm_04', 'Проектная деятельность', 'Политический менеджмент'),
                ('pm_05', 'Партийная принадлежность сотрудников', 'Политический менеджмент'),
                ('pm_06', 'Распределение мандатов', 'Политический менеджмент'),
                ('pm_07', 'Показатели АГП (Уровень)', 'Политический менеджмент'),
                ('pm_08', 'Показатели АГП (Качество)', 'Политический менеджмент'),
                ('pm_09', 'Экономическая привлекательность МО', 'Политический менеджмент'),
                ('ca_01', 'Вовлеченность молодежи (Добровольчество)', 'Забота и внимание'),
                ('ca_02', 'Вовлеченность молодежи (Движение Первых)', 'Забота и внимание'),
                ('ca_03', 'Личная работа главы с ветеранами СВО', 'Забота и внимание'),
                ('ca_04', 'Партийная принадлежность ветеранов СВО', 'Забота и внимание'),
                ('dev_01', 'Кадровый управленческий резерв', 'Развитие кадрового и проектного потенциала МО'),
                ('dev_02', 'Работа с грантами', 'Развитие кадрового и проектного потенциала МО'),
                ('dev_03', 'Участие в проекте «Гордость Липецкой земли»', 'Развитие кадрового и проектного потенциала МО'),
                ('pen_01', 'Конфликты с региональной властью', 'Штрафные критерии'),
                ('pen_02', 'Внутримуниципальные конфликты', 'Штрафные критерии'),
                ('pen_03', 'Данные правоохранительных органов', 'Штрафные критерии'),
            ]

            for code, name, block in proper_indicators:
                session.execute(text("""
                    INSERT INTO dim_indicator (code, name, block, is_public, weight)
                    VALUES (:code, :name, :block, true, 1.0)
                    ON CONFLICT (code) DO NOTHING
                """), {'code': code, 'name': name, 'block': block})

            session.commit()
            logger.info("✓ Inserted 19 proper indicators")

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

        else:
            logger.info("✓ All indicators already have proper codes, skipping migration")

        session.close()

    except Exception as e:
        logger.error(f"✗ Ensure proper indicator codes migration failed: {str(e)}")
        try:
            session.rollback()
            session.close()
        except:
            pass



def implement_official_methodology():
    """Implement official methodology: 16 criteria"""
    logger.info("🔄 Running migration: Implement official methodology...")
    try:
        session = SessionLocal()
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN rating_type VARCHAR(50)"))
        except:
            pass
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN is_penalty BOOLEAN DEFAULT FALSE"))
        except:
            pass
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN max_points INTEGER"))
        except:
            pass
        session.commit()
        
        official_count = session.query(DimIndicator).filter(
            DimIndicator.code.in_(['pub_1','pub_2','pub_3','pub_4','pub_5','pub_6','pub_7','pub_8','pub_9',
                'closed_1','closed_2','closed_3','closed_4','closed_5','closed_6','closed_7','closed_8',
                'pen_1','pen_2','pen_3'])
        ).count()
        
        if official_count < 16:
            logger.info("Creating official 16 criteria...")
            public_criteria = [
                DimIndicator(code='pub_1', name='Поддержка руководства области', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_2', name='Выполнение задач АГП', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=5),
                DimIndicator(code='pub_3', name='Позиционирование главы МО', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_4', name='Проектная деятельность главы', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_5', name='Молодежь в добровольчестве', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_6', name='Молодежь в Движении Первых', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_7', name='Работа с ветеранами СВО', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_8', name='Кадровый управленческий резерв', block='Развитие кадрового потенциала', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_9', name='Работа с грантами', block='Развитие кадрового потенциала', rating_type='ПУБЛИЧНЫЙ', max_points=3),
            ]
            closed_criteria = [
                DimIndicator(code='closed_1', name='Партийное мнение в администрации', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=6),
                DimIndicator(code='closed_2', name='Альтернативное мнение в органе', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=4),
                DimIndicator(code='closed_3', name='Целевые показатели АГП (уровень)', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=5),
                DimIndicator(code='closed_4', name='Целевые показатели АГП (качество)', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=5),
                DimIndicator(code='closed_5', name='Экономическая привлекательность МО', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=3),
                DimIndicator(code='closed_6', name='Работа с ветеранами СВО', block='Забота и внимание', rating_type='ЗАКРЫТЫЙ', max_points=3),
                DimIndicator(code='closed_7', name='Политическая деятельность ветеранов', block='Забота и внимание', rating_type='ЗАКРЫТЫЙ', max_points=6),
                DimIndicator(code='closed_8', name='Проект Гордость Липецкой земли', block='Развитие кадрового потенциала', rating_type='ЗАКРЫТЫЙ', max_points=2),
            ]
            penalty_criteria = [
                DimIndicator(code='pen_1', name='Конфликты с региональной властью', block='Штрафные критерии', max_points=-3, is_penalty=True),
                DimIndicator(code='pen_2', name='Внутримуниципальные конфликты', block='Штрафные критерии', max_points=-3, is_penalty=True),
                DimIndicator(code='pen_3', name='Правоохранительные органы', block='Штрафные критерии', max_points=-5, is_penalty=True),
            ]
            for criterion in public_criteria + closed_criteria + penalty_criteria:
                session.add(criterion)
            session.commit()
            logger.info("✓ Created 16 official criteria")
        else:
            logger.info("✓ Official methodology indicators already exist")
        session.close()
    except Exception as e:
        logger.error(f"✗ Official methodology migration failed: {str(e)}")
        try:
            session.rollback()
            session.close()
        except:
            pass


def implement_official_methodology():
    """Implement official methodology: 16 criteria"""
    logger.info("Running migration: Implement official methodology...")
    try:
        session = SessionLocal()
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN rating_type VARCHAR(50)"))
        except:
            pass
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN is_penalty BOOLEAN DEFAULT FALSE"))
        except:
            pass
        try:
            session.execute(text("ALTER TABLE dim_indicator ADD COLUMN max_points INTEGER"))
        except:
            pass
        session.commit()
        
        official_count = session.query(DimIndicator).filter(
            DimIndicator.code.in_(['pub_1','pub_2','pub_3','pub_4','pub_5','pub_6','pub_7','pub_8','pub_9',
                'closed_1','closed_2','closed_3','closed_4','closed_5','closed_6','closed_7','closed_8',
                'pen_1','pen_2','pen_3'])
        ).count()
        
        if official_count < 16:
            logger.info("Creating official 16 criteria...")
            public_criteria = [
                DimIndicator(code='pub_1', name='Поддержка руководства области', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_2', name='Выполнение задач АГП', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=5),
                DimIndicator(code='pub_3', name='Позиционирование главы МО', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_4', name='Проектная деятельность главы', block='Политический менеджмент', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_5', name='Молодежь в добровольчестве', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_6', name='Молодежь в Движении Первых', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_7', name='Работа с ветеранами СВО', block='Забота и внимание', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_8', name='Кадровый управленческий резерв', block='Развитие кадрового потенциала', rating_type='ПУБЛИЧНЫЙ', max_points=3),
                DimIndicator(code='pub_9', name='Работа с грантами', block='Развитие кадрового потенциала', rating_type='ПУБЛИЧНЫЙ', max_points=3),
            ]
            closed_criteria = [
                DimIndicator(code='closed_1', name='Партийное мнение в администрации', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=6),
                DimIndicator(code='closed_2', name='Альтернативное мнение в органе', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=4),
                DimIndicator(code='closed_3', name='Целевые показатели АГП (уровень)', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=5),
                DimIndicator(code='closed_4', name='Целевые показатели АГП (качество)', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=5),
                DimIndicator(code='closed_5', name='Экономическая привлекательность МО', block='Политический менеджмент', rating_type='ЗАКРЫТЫЙ', max_points=3),
                DimIndicator(code='closed_6', name='Работа с ветеранами СВО', block='Забота и внимание', rating_type='ЗАКРЫТЫЙ', max_points=3),
                DimIndicator(code='closed_7', name='Политическая деятельность ветеранов', block='Забота и внимание', rating_type='ЗАКРЫТЫЙ', max_points=6),
                DimIndicator(code='closed_8', name='Проект Гордость Липецкой земли', block='Развитие кадрового потенциала', rating_type='ЗАКРЫТЫЙ', max_points=2),
            ]
            penalty_criteria = [
                DimIndicator(code='pen_1', name='Конфликты с региональной властью', block='Штрафные критерии', max_points=-3, is_penalty=True),
                DimIndicator(code='pen_2', name='Внутримуниципальные конфликты', block='Штрафные критерии', max_points=-3, is_penalty=True),
                DimIndicator(code='pen_3', name='Правоохранительные органы', block='Штрафные критерии', max_points=-5, is_penalty=True),
            ]
            for criterion in public_criteria + closed_criteria + penalty_criteria:
                session.add(criterion)
            session.commit()
            logger.info("Created 16 official criteria")
        else:
            logger.info("Official methodology indicators already exist")
        session.close()
    except Exception as e:
        logger.error(f"Official methodology migration failed: {str(e)}")
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
    apply_dim_indicator_columns_migration()     # Fix dim_indicator table structure
    apply_leader_name_column_migration()        # Add leader_name column and data
    apply_criteria_blocks_migration()           # Create criteria blocks
    ensure_proper_indicator_codes()             # Ensure indicators have proper codes (pm_*, ca_*, etc)
    fix_fact_indicator_scores()                 # Fix NULL scores in fact_indicator
    implement_official_methodology()                 # Implement official methodology

    logger.info("=" * 80)
    logger.info("✓ All migrations completed")
    logger.info("=" * 80)
