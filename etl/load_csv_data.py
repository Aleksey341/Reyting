"""
ETL Script to load CSV data from source zip into the database.
Processes the Оценка_поддержки_руководителя_v1 data.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dashboard_user:dashboard_password@localhost:5432/dashboard_db"
)

# Import models from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from models import (
    DimMO, DimPeriod, DimIndicator, DimMethodology, SrcRegistry,
    FactIndicator, Base
)


class CSVLoader:
    """Load CSV data into database"""

    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def load_mos(self):
        """Load municipal organizations"""
        logger.info("Loading municipal organizations...")

        mos_data = [
            ("Липецк", "4800000"),
            ("Елец", "4801000"),
            ("Воловский", "4802000"),
            ("Грязянский", "4803000"),
            ("Данковский", "4804000"),
            ("Добринский", "4805000"),
            ("Добровский", "4806000"),
            ("Долгоруковский", "4807000"),
            ("Елецкий", "4808000"),
            ("Задонский", "4809000"),
            ("Измалковский", "4810000"),
            ("Краснинский", "4811000"),
            ("Лебедянский", "4812000"),
            ("Лев-Толстовский", "4813000"),
            ("Липецкий", "4814000"),
            ("Становлянский", "4815000"),
            ("Тербунский", "4816000"),
            ("Усманский", "4817000"),
            ("Хлевенский", "4818000"),
            ("Чаплыгинский", "4819000"),
        ]

        for name, oktmo in mos_data:
            existing = self.session.query(DimMO).filter(DimMO.mo_name == name).first()
            if not existing:
                mo = DimMO(mo_name=name, oktmo=oktmo)
                self.session.add(mo)
                logger.info(f"Added MO: {name}")

        self.session.commit()
        logger.info(f"Loaded {len(mos_data)} municipal organizations")

    def load_periods(self):
        """Load periods (months, halfyears, years)"""
        logger.info("Loading periods...")

        # Create months for 2023-2024
        for year in [2023, 2024]:
            for month in range(1, 13):
                date_from = datetime(year, month, 1).date()
                if month == 12:
                    date_to = datetime(year + 1, 1, 1).date() - timedelta(days=1)
                else:
                    date_to = datetime(year, month + 1, 1).date() - timedelta(days=1)

                period_key = f"{year}-{month:02d}"
                existing = self.session.query(DimPeriod).filter(
                    DimPeriod.period_type == 'month',
                    DimPeriod.date_from == date_from
                ).first()

                if not existing:
                    period = DimPeriod(
                        period_type='month',
                        date_from=date_from,
                        date_to=date_to,
                        edg_flag=False
                    )
                    self.session.add(period)

        self.session.commit()
        logger.info("Loaded periods")

    def load_indicators(self):
        """Load indicators from methodology"""
        logger.info("Loading indicators...")

        indicators_data = [
            ("support_leadership", "Поддержка со стороны руководства области", "Полит. менеджмент", 0, 3),
            ("agp_tasks", "Эффективность выполнения задач АГП", "Полит. менеджмент", 0, 5),
            ("positioning", "Уникальное позиционирование главы", "Полит. менеджмент", 0, 3),
            ("projects", "Проектная деятельность главы", "Полит. менеджмент", 0, 3),
            ("youth_volunteers", "Доля молодёжи в добровольчестве", "Забота и внимание", 0, 3),
            ("movement_first", "Дети в Движении Первых", "Забота и внимание", 0, 3),
            ("veterans_involvement", "Вовлечённость с ветеранами/семьями СВО", "Забота и внимание", 0, 3),
            ("cadre_reserve", "Формирование кадрового резерва", "Развитие кадрового потенциала", 0, 3),
            ("grants", "Эффективность работы с грантами", "Развитие кадрового потенциала", 0, 3),
        ]

        for code, name, block, min_val, max_val in indicators_data:
            existing = self.session.query(DimIndicator).filter(DimIndicator.code == code).first()
            if not existing:
                indicator = DimIndicator(
                    code=code,
                    name=name,
                    block=block,
                    is_public=True,
                    min_value=min_val,
                    max_value=max_val
                )
                self.session.add(indicator)
                logger.info(f"Added indicator: {code}")

        self.session.commit()
        logger.info("Loaded indicators")

    def load_methodology(self):
        """Load methodology version"""
        logger.info("Loading methodology...")

        existing = self.session.query(DimMethodology).filter(
            DimMethodology.version == "1.0"
        ).first()

        if not existing:
            methodology = DimMethodology(
                version="1.0",
                valid_from=datetime(2024, 1, 1).date(),
                notes="Методика оценки поддержки руководства v1.0"
            )
            self.session.add(methodology)
            self.session.commit()
            logger.info("Added methodology v1.0")

    def load_sources(self):
        """Load data sources"""
        logger.info("Loading data sources...")

        sources_data = [
            ("csv_support", "CSV Source", "support@example.com", "Excel", "monthly"),
            ("api_indicators", "API Indicators", "api@example.com", "API", "monthly"),
            ("manual_input", "Manual Input", "operator@example.com", "Manual", "on-demand"),
        ]

        for code, org, contact, channel, schedule in sources_data:
            existing = self.session.query(SrcRegistry).filter(SrcRegistry.code == code).first()
            if not existing:
                source = SrcRegistry(
                    code=code,
                    org=org,
                    contact=contact,
                    channel=channel,
                    schedule=schedule
                )
                self.session.add(source)
                logger.info(f"Added source: {code}")

        self.session.commit()
        logger.info("Loaded data sources")

    def run(self):
        """Run all loading operations"""
        try:
            logger.info("Starting data load...")
            self.load_mos()
            self.load_periods()
            self.load_indicators()
            self.load_methodology()
            self.load_sources()
            logger.info("Data load completed successfully!")
        except Exception as e:
            logger.error(f"Error during data load: {str(e)}")
            self.session.rollback()
            raise
        finally:
            self.session.close()


if __name__ == "__main__":
    loader = CSVLoader(DATABASE_URL)
    loader.run()
