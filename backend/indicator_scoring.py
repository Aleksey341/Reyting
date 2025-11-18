#!/usr/bin/env python3
"""
Indicator Scoring Logic - Simplified Version

Converts raw Excel data into numeric scores for each official methodology indicator.
Uses a simpler, more robust approach that doesn't depend on exact column names.
"""

import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IndicatorScorer:
    """Calculates indicator scores based on official methodology rules."""

    @staticmethod
    def _get_data_columns(row: pd.Series) -> list:
        """Get non-header columns (skip Муниципалитет, Глава МО, etc.)"""
        skip_patterns = ['муниципалитет', 'глава', 'мо', 'fio', 'name', 'фио']
        return [col for col in row.index
                if not any(skip.lower() in str(col).lower() for skip in skip_patterns)]

    @staticmethod
    def _count_yes_values(row: pd.Series, limit: int = None) -> int:
        """Count "Да" values in numeric columns, up to limit"""
        data_cols = IndicatorScorer._get_data_columns(row)
        count = 0

        for col in data_cols:
            if limit and count >= limit:
                break

            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    count += 1

        return count

    @staticmethod
    def _get_numeric_values(row: pd.Series) -> list:
        """Get all numeric values from data columns"""
        data_cols = IndicatorScorer._get_data_columns(row)
        values = []

        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                try:
                    # Try to convert to float
                    num_val = float(val)
                    values.append(num_val)
                except (ValueError, TypeError):
                    pass

        return values

    @staticmethod
    def _get_first_text_value(row: pd.Series) -> Optional[str]:
        """Get first text (non-numeric) value from data columns"""
        data_cols = IndicatorScorer._get_data_columns(row)

        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                # Check if it's not a number
                try:
                    float(val_str)
                    continue  # Skip numeric values
                except ValueError:
                    if val_str and val_str not in ['да', 'нет']:  # Skip да/нет for now
                        return val_str

        return None

    # ============ PUBLIC INDICATORS (pub_1 to pub_9) ============

    @staticmethod
    def score_pub_1(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_1: Support (3 yes/no questions) -> 0-3"""
        count = IndicatorScorer._count_yes_values(row, limit=3)
        if count == 0:
            logger.debug(f"pub_1: Found {count} 'да' values")
            return None
        logger.debug(f"pub_1: score = {count}")
        return float(count)

    @staticmethod
    def score_pub_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_2: Task execution (numeric %) -> 0-5"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]  # Take first numeric value
        # Normalize to 0-1 if percentage
        if val > 1:
            val = val / 100

        score = val * 5
        logger.debug(f"pub_2: value={val}, score={score}")
        return min(score, 5.0)

    @staticmethod
    def score_pub_3(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_3: Head positioning (categorical) -> 0-3"""
        text = IndicatorScorer._get_first_text_value(row)
        if not text:
            return None

        if 'функционер' in text or 'хозяйственник' in text:
            logger.debug(f"pub_3: '{text}' -> 3.0")
            return 3.0
        elif 'размытое' in text or 'некачественное' in text:
            logger.debug(f"pub_3: '{text}' -> 0.0")
            return 0.0

        return None

    @staticmethod
    def score_pub_4(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_4: Project activity (numeric) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        score = min(val / 2, 3.0)
        logger.debug(f"pub_4: value={val}, score={score}")
        return score

    @staticmethod
    def score_pub_5(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_5: Youth volunteering (numeric %) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        if val > 1:
            val = val / 100

        score = min(val * 3, 3.0)
        logger.debug(f"pub_5: value={val}, score={score}")
        return score

    @staticmethod
    def score_pub_6(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_6: Youth in First Movement (numeric) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        score = min(val / 100, 3.0)
        logger.debug(f"pub_6: value={val}, score={score}")
        return score

    @staticmethod
    def score_pub_7(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_7: Veterans work (3 metrics: count, %, %) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if len(values) < 3:
            logger.debug(f"pub_7: Need 3 numeric values, found {len(values)}")
            return None

        # First: meetings count -> /20 (max 1.0)
        meet_score = min(values[0] / 20, 1.0)

        # Second: participation %
        particip = values[1]
        if particip > 1:
            particip = particip / 100
        particip_score = min(particip, 1.0)

        # Third: solutions %
        solution = values[2]
        if solution > 1:
            solution = solution / 100
        solution_score = min(solution, 1.0)

        score = min(meet_score + particip_score + solution_score, 3.0)
        logger.debug(f"pub_7: meets={meet_score:.2f}, particip={particip_score:.2f}, solutions={solution_score:.2f}, score={score:.2f}")
        return score

    @staticmethod
    def score_pub_8(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_8: Cadre reserve (numeric) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        score = min(val / 5, 3.0)
        logger.debug(f"pub_8: value={val}, score={score}")
        return score

    @staticmethod
    def score_pub_9(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_9: Grants work (wins + volume + violations) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        data_cols = IndicatorScorer._get_data_columns(row)

        score = 0.0

        # First numeric: wins
        if len(values) > 0:
            score += min(values[0] / 3, 1.5)

        # Second numeric: volume (skip if looks like date)
        if len(values) > 1 and values[1] < 5000:  # Reasonable млн range
            score += min(values[1] / 100 * 1.5, 1.5)

        # Find да/нет for violations
        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    score -= 2.0
                    break
                elif val_str == 'нет':
                    score += 1.0
                    break

        score = max(min(score, 3.0), 0.0)
        logger.debug(f"pub_9: score={score}")
        return score

    # ============ CLOSED INDICATORS (closed_1 to closed_8) ============

    @staticmethod
    def score_closed_1(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_1: Party opinion (% members + % supporters) -> 0-6"""
        values = IndicatorScorer._get_numeric_values(row)
        if len(values) < 3:  # Need: total, members %, supporters %
            return None

        # Skip first (total count), use % values
        members = values[1] if len(values) > 1 else 0
        supporters = values[2] if len(values) > 2 else 0

        if members > 1:
            members = members / 100
        if supporters > 1:
            supporters = supporters / 100

        score = min((members * 3) + (supporters * 3), 6.0)
        logger.debug(f"closed_1: members={members:.2f}, supporters={supporters:.2f}, score={score}")
        return score

    @staticmethod
    def score_closed_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_2: Alternative mandates (numeric %) -> 0-4"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        if val > 1:
            val = val / 100

        score = min(val * 4, 4.0)
        logger.debug(f"closed_2: value={val}, score={score}")
        return score

    @staticmethod
    def score_closed_3(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_3: AGP targets (level) -> 0-5"""
        text = IndicatorScorer._get_first_text_value(row)
        if not text:
            return None

        if 'превысил' in text:
            logger.debug(f"closed_3: '{text}' -> 5.0")
            return 5.0
        elif 'выполнен' in text and 'не' not in text:
            logger.debug(f"closed_3: '{text}' -> 3.0")
            return 3.0
        else:
            logger.debug(f"closed_3: '{text}' -> 0.0")
            return 0.0

    @staticmethod
    def score_closed_4(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_4: AGP targets (quality) -> 0-5"""
        text = IndicatorScorer._get_first_text_value(row)
        if not text:
            return None

        if 'превышает' in text or 'превышен' in text:
            logger.debug(f"closed_4: '{text}' -> 5.0")
            return 5.0
        elif 'достигнут' in text and 'не' not in text:
            logger.debug(f"closed_4: '{text}' -> 3.0")
            return 3.0
        else:
            logger.debug(f"closed_4: '{text}' -> 0.0")
            return 0.0

    @staticmethod
    def score_closed_5(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_5: Economic attractiveness -> 0-3"""
        text = IndicatorScorer._get_first_text_value(row)
        if not text:
            return None

        if 'высокая' in text:
            logger.debug(f"closed_5: '{text}' -> 3.0")
            return 3.0
        elif 'средняя' in text:
            logger.debug(f"closed_5: '{text}' -> 2.0")
            return 2.0
        elif 'низкая' in text or 'слабая' in text:
            logger.debug(f"closed_5: '{text}' -> 1.0")
            return 1.0

        return None

    @staticmethod
    def score_closed_7(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_7: Veterans political activity (%) -> 0-6"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        val = values[0]
        if val > 1:
            val = val / 100

        score = min(val * 6, 6.0)
        logger.debug(f"closed_7: value={val}, score={score}")
        return score

    @staticmethod
    def score_closed_8(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_8: Pride project -> 0-3"""
        data_cols = IndicatorScorer._get_data_columns(row)

        # Try да/нет first
        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    logger.debug(f"closed_8: да -> 3.0")
                    return 3.0
                elif val_str == 'нет':
                    logger.debug(f"closed_8: нет -> 0.0")
                    return 0.0

        # Try numeric
        values = IndicatorScorer._get_numeric_values(row)
        if values:
            score = min(values[0] / 5, 3.0)
            logger.debug(f"closed_8: value={values[0]}, score={score}")
            return score

        return None

    # ============ PENALTY INDICATORS (pen_1 to pen_3) ============

    @staticmethod
    def score_pen_1(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_1: Regional conflicts (2 yes/no) -> -5 to +2"""
        data_cols = IndicatorScorer._get_data_columns(row)
        score = 0.0
        count = 0

        for col in data_cols:
            if count >= 2:
                break

            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    if count == 0:
                        score += -3.0  # Public conflict
                    else:
                        score += -2.0  # Professional conflict
                elif val_str == 'нет':
                    score += 1.0

                count += 1

        if count < 2:
            logger.debug(f"pen_1: Only found {count} да/нет values, need 2")
            return None

        logger.debug(f"pen_1: score={score}")
        return score

    @staticmethod
    def score_pen_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_2: Internal conflicts (count) -> -3 to +1"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            return None

        count = int(values[0])
        if count >= 1:
            score = -2.0
        else:
            score = 1.0

        logger.debug(f"pen_2: count={count}, score={score}")
        return score

    @staticmethod
    def score_pen_3(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_3: Law enforcement data (3 yes/no) -> -8 to +3"""
        data_cols = IndicatorScorer._get_data_columns(row)
        score = 0.0
        count = 0

        for col in data_cols:
            if count >= 3:
                break

            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    if count == 0:
                        score += -5.0  # Criminal case
                    elif count == 1:
                        score += -2.0  # Inspections
                    else:
                        score += -1.0  # Publications
                elif val_str == 'нет':
                    score += 1.0

                count += 1

        if count < 3:
            logger.debug(f"pen_3: Only found {count} да/нет values, need 3")
            return None

        logger.debug(f"pen_3: score={score}")
        return score

    # ============ MAIN SCORING METHOD ============

    @classmethod
    def score_indicator(cls, indicator_code: str, row: pd.Series) -> Optional[float]:
        """Score any indicator"""
        scoring_func = getattr(cls, f"score_{indicator_code}", None)

        if not scoring_func:
            logger.warning(f"No scoring function for {indicator_code}")
            return None

        try:
            score = scoring_func(row, {})

            if score is not None:
                logger.info(f"{indicator_code}: score = {score}")
            else:
                logger.debug(f"{indicator_code}: returned None")

            return score
        except Exception as e:
            logger.error(f"Error scoring {indicator_code}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
