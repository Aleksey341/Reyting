"""
Unit tests for closed_8 criterion fix
Ensures that the Closed Rating maximum is correctly set to 35 points

Bug Fix: closed_8 was incorrectly set to max_points=2, should be 3
Related Issue: https://github.com/Aleksey341/Reyting/issues/XXX
Date: 2025-11-18
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from models import DimIndicator


class TestClosed8Criterion:
    """Test suite for closed_8 criterion fix"""

    @pytest.fixture
    def db_session(self):
        """Create database session for tests"""
        session = SessionLocal()
        yield session
        session.close()

    def test_closed_8_max_points_is_3(self, db_session: Session):
        """Verify that closed_8 has max_points = 3"""
        indicator = db_session.query(DimIndicator).filter(
            DimIndicator.code == 'closed_8'
        ).first()

        assert indicator is not None, "closed_8 criterion not found in database"
        assert indicator.max_points == 3, (
            f"closed_8 max_points should be 3, got {indicator.max_points}"
        )

    def test_closed_8_correct_name(self, db_session: Session):
        """Verify that closed_8 has correct name"""
        indicator = db_session.query(DimIndicator).filter(
            DimIndicator.code == 'closed_8'
        ).first()

        expected_name = 'Проект Гордость Липецкой земли'
        assert indicator.name == expected_name, (
            f"closed_8 name should be '{expected_name}', got '{indicator.name}'"
        )

    def test_closed_8_rating_type(self, db_session: Session):
        """Verify that closed_8 is marked as CLOSED rating"""
        indicator = db_session.query(DimIndicator).filter(
            DimIndicator.code == 'closed_8'
        ).first()

        assert indicator.rating_type == 'ЗАКРЫТЫЙ', (
            f"closed_8 rating_type should be 'ЗАКРЫТЫЙ', got '{indicator.rating_type}'"
        )

    def test_closed_8_is_not_penalty(self, db_session: Session):
        """Verify that closed_8 is not marked as penalty criterion"""
        indicator = db_session.query(DimIndicator).filter(
            DimIndicator.code == 'closed_8'
        ).first()

        assert indicator.is_penalty is False, (
            "closed_8 should not be marked as penalty criterion"
        )

    def test_closed_rating_maximum_is_35(self, db_session: Session):
        """Verify that closed rating has maximum of 35 points"""
        total = db_session.query(func.sum(DimIndicator.max_points)).filter(
            DimIndicator.rating_type == 'ЗАКРЫТЫЙ'
        ).scalar()

        assert total == 35, (
            f"Closed rating maximum should be 35 points, got {total}. "
            "This likely means closed_8 is still incorrectly set to 2 instead of 3."
        )

    def test_public_rating_maximum_is_31(self, db_session: Session):
        """Verify that public rating has maximum of 31 points"""
        total = db_session.query(func.sum(DimIndicator.max_points)).filter(
            DimIndicator.rating_type == 'ПУБЛИЧНЫЙ'
        ).scalar()

        assert total == 31, (
            f"Public rating maximum should be 31 points, got {total}"
        )

    def test_penalty_maximum_is_minus_11(self, db_session: Session):
        """Verify that penalty criteria sum to -11 (can reduce by up to 10)"""
        total = db_session.query(func.sum(DimIndicator.max_points)).filter(
            DimIndicator.is_penalty == True
        ).scalar()

        assert total == -11, (
            f"Penalty criteria should sum to -11, got {total}"
        )

    def test_overall_maximum_is_66(self, db_session: Session):
        """Verify that overall rating maximum is 66 points (31+35)"""
        public_total = db_session.query(func.sum(DimIndicator.max_points)).filter(
            DimIndicator.rating_type == 'ПУБЛИЧНЫЙ'
        ).scalar()

        closed_total = db_session.query(func.sum(DimIndicator.max_points)).filter(
            DimIndicator.rating_type == 'ЗАКРЫТЫЙ'
        ).scalar()

        overall_max = public_total + closed_total
        assert overall_max == 66, (
            f"Overall rating maximum should be 66 (31+35), got {overall_max}. "
            "This is likely due to closed_8 being incorrectly set."
        )

    def test_all_closed_criteria_exist(self, db_session: Session):
        """Verify that all 8 closed criteria exist"""
        closed_codes = [
            'closed_1', 'closed_2', 'closed_3', 'closed_4',
            'closed_5', 'closed_6', 'closed_7', 'closed_8'
        ]

        for code in closed_codes:
            indicator = db_session.query(DimIndicator).filter(
                DimIndicator.code == code
            ).first()
            assert indicator is not None, f"Closed criterion {code} not found"

    def test_closed_criteria_distribution(self, db_session: Session):
        """Verify the distribution of points across closed criteria"""
        expected_points = {
            'closed_1': 6,
            'closed_2': 4,
            'closed_3': 5,
            'closed_4': 5,
            'closed_5': 3,
            'closed_6': 3,
            'closed_7': 6,
            'closed_8': 3,  # This is the fix!
        }

        for code, expected_max in expected_points.items():
            indicator = db_session.query(DimIndicator).filter(
                DimIndicator.code == code
            ).first()
            assert indicator.max_points == expected_max, (
                f"{code} should have max_points={expected_max}, "
                f"got {indicator.max_points}"
            )


class TestMethodologyIntegrity:
    """Test that the entire methodology is correctly implemented"""

    @pytest.fixture
    def db_session(self):
        """Create database session for tests"""
        session = SessionLocal()
        yield session
        session.close()

    def test_all_16_criteria_exist(self, db_session: Session):
        """Verify all 16 official criteria are in database"""
        official_codes = [
            'pub_1', 'pub_2', 'pub_3', 'pub_4', 'pub_5', 'pub_6', 'pub_7', 'pub_8', 'pub_9',
            'closed_1', 'closed_2', 'closed_3', 'closed_4', 'closed_5', 'closed_6', 'closed_7', 'closed_8',
            'pen_1', 'pen_2', 'pen_3'
        ]

        count = db_session.query(DimIndicator).filter(
            DimIndicator.code.in_(official_codes)
        ).count()

        assert count == len(official_codes), (
            f"Expected {len(official_codes)} official criteria, found {count}"
        )

    def test_no_non_penalty_criteria_have_negative_points(self, db_session: Session):
        """Verify that only penalty criteria have negative points"""
        negative_non_penalty = db_session.query(DimIndicator).filter(
            DimIndicator.is_penalty == False,
            DimIndicator.max_points < 0
        ).all()

        assert len(negative_non_penalty) == 0, (
            f"Found {len(negative_non_penalty)} non-penalty criteria with negative points: "
            f"{[c.code for c in negative_non_penalty]}"
        )

    def test_penalty_criteria_all_negative(self, db_session: Session):
        """Verify that all penalty criteria have negative points"""
        positive_penalty = db_session.query(DimIndicator).filter(
            DimIndicator.is_penalty == True,
            DimIndicator.max_points >= 0
        ).all()

        assert len(positive_penalty) == 0, (
            f"Found {len(positive_penalty)} penalty criteria with non-negative points: "
            f"{[c.code for c in positive_penalty]}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
