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
        # Skip columns that are metadata/headers only
        # Use word boundaries or exact matches for more precision
        skip_patterns = [
            'муниципалитет',    # exact municipality column
            'глава мо',         # exact "head of MO" column
            'фио',              # name (full name)
            'name',             # english name
            '№', 'no.',         # numbering columns
            'unnamed',          # auto-generated unnamed columns
            'index'             # index columns
        ]

        data_cols = []
        for col in row.index:
            col_str = str(col).strip().lower()

            # Check for exact matches or word-boundary matches
            skip = False
            for pattern in skip_patterns:
                # For short patterns like 'мо', require word boundaries
                if pattern in ['мо']:
                    # Check if it's a whole word
                    import re
                    if re.search(r'\b' + re.escape(pattern) + r'\b', col_str):
                        skip = True
                        break
                else:
                    # For longer patterns, substring match is OK
                    if pattern in col_str:
                        skip = True
                        break

            if skip:
                continue

            # Skip NaN columns
            if pd.isna(row[col]) or row[col] == '':
                continue

            data_cols.append(col)

        return data_cols

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
            logger.debug(f"pub_1: Found {count} 'да' values, treating as 0")
            return 0.0
        logger.debug(f"pub_1: score = {count}")
        return float(count)

    @staticmethod
    def score_pub_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_2: Task execution (numeric %) -> 0-5 (max)"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            logger.debug(f"pub_2: No numeric values found")
            return 0.0

        val = values[0]  # Take first numeric value
        # Normalize to 0-1 if percentage
        if val > 1:
            val = val / 100

        # Scoring: 91-100% -> 5, 81-90% -> 4, 71-80% -> 3, 61-70% -> 2, 51-60% -> 1, <50% -> 0
        if val >= 0.91:
            score = 5.0
        elif val >= 0.81:
            score = 4.0
        elif val >= 0.71:
            score = 3.0
        elif val >= 0.61:
            score = 2.0
        elif val >= 0.51:
            score = 1.0
        else:
            score = 0.0

        logger.debug(f"pub_2: value={val:.2%}, score={score}")
        return score

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
            logger.debug(f"pub_5: No numeric values found")
            return 0.0

        val = values[0]
        if val > 1:
            val = val / 100

        # Scoring: >50% -> 3, 26-50% -> 2, 16-25% -> 1, <15% -> 0
        if val > 0.50:
            score = 3.0
        elif val >= 0.26:
            score = 2.0
        elif val >= 0.16:
            score = 1.0
        else:
            score = 0.0

        logger.debug(f"pub_5: value={val:.2%}, score={score}")
        return score

    @staticmethod
    def score_pub_6(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_6: Youth in First Movement (numeric %) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            logger.debug(f"pub_6: No numeric values found")
            return 0.0

        val = values[0]
        if val > 1:
            val = val / 100

        # Scoring: >50% -> 3, 26-50% -> 2, 16-25% -> 1, <15% -> 0
        if val > 0.50:
            score = 3.0
        elif val >= 0.26:
            score = 2.0
        elif val >= 0.16:
            score = 1.0
        else:
            score = 0.0

        logger.debug(f"pub_6: value={val:.2%}, score={score}")
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
        """pub_8: Cadre reserve (numeric %) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            logger.debug(f"pub_8: No numeric values found")
            return 0.0

        val = values[0]
        if val > 1:
            val = val / 100

        # Scoring: 80-100% -> 3, 50-79% -> 2, 30-49% -> 1
        if val >= 0.80:
            score = 3.0
        elif val >= 0.50:
            score = 2.0
        elif val >= 0.30:
            score = 1.0
        else:
            score = 0.0

        logger.debug(f"pub_8: value={val:.2%}, score={score}")
        return score

    @staticmethod
    def score_pub_9(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pub_9: Grants work (wins + volume + violations) -> 0-3"""
        values = IndicatorScorer._get_numeric_values(row)
        data_cols = IndicatorScorer._get_data_columns(row)

        if not values:
            logger.debug(f"pub_9: No numeric values found")
            return 0.0

        score = 0.0

        # First numeric: wins count
        if len(values) > 0:
            wins = values[0]
            # 3+ wins -> 1.5, 2 wins -> 1.0, 1 win -> 0.5
            if wins >= 3:
                score += 1.5
            elif wins >= 2:
                score += 1.0
            elif wins >= 1:
                score += 0.5

        # Second numeric: volume (млн руб)
        if len(values) > 1:
            volume = values[1]
            # >= 10 млн -> 1.5, >= 1 млн -> 1.0
            if volume >= 10:
                score += 1.5
            elif volume >= 1:
                score += 1.0

        # Find да/нет for violations
        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    score -= 2.0
                    break
                elif val_str == 'нет':
                    score += 0.5
                    break

        score = max(min(score, 3.0), 0.0)
        logger.debug(f"pub_9: wins={values[0] if values else 0}, volume={values[1] if len(values) > 1 else 0}, score={score}")
        return score

    # ============ CLOSED INDICATORS (closed_1 to closed_8) ============

    @staticmethod
    def score_closed_1(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_1: Party opinion (% members + % supporters) -> 0-6"""
        values = IndicatorScorer._get_numeric_values(row)
        if len(values) < 2:
            logger.debug(f"closed_1: Need 2 numeric values (members%, supporters%), found {len(values)}")
            return 0.0

        # Take first two numeric values as % members and % supporters
        members = values[0]
        supporters = values[1] if len(values) > 1 else 0

        if members > 1:
            members = members / 100
        if supporters > 1:
            supporters = supporters / 100

        # Scoring: members % * 3 + supporters % * 3
        score = min((members * 3) + (supporters * 3), 6.0)
        logger.debug(f"closed_1: members={members:.2%}, supporters={supporters:.2%}, score={score:.1f}")
        return score

    @staticmethod
    def score_closed_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_2: Alternative mandates (numeric %) -> 0-4"""
        values = IndicatorScorer._get_numeric_values(row)
        if not values:
            logger.debug(f"closed_2: No numeric values found")
            return 0.0

        val = values[0]
        if val > 1:
            val = val / 100

        # Scoring: 100% -> 4, 94-99% -> 2, <94% -> 0
        if val >= 1.0:
            score = 4.0
        elif val >= 0.94:
            score = 2.0
        else:
            score = 0.0

        logger.debug(f"closed_2: value={val:.2%}, score={score}")
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
        """closed_7: Veterans political activity (% members + % supporters) -> 0-6"""
        values = IndicatorScorer._get_numeric_values(row)
        if len(values) < 2:
            logger.debug(f"closed_7: Need 2 numeric values, found {len(values)}")
            return 0.0

        members = values[0]
        supporters = values[1] if len(values) > 1 else 0

        if members > 1:
            members = members / 100
        if supporters > 1:
            supporters = supporters / 100

        # Scoring: members % * 3 + supporters % * 3
        score = min((members * 3) + (supporters * 3), 6.0)
        logger.debug(f"closed_7: members={members:.2%}, supporters={supporters:.2%}, score={score:.1f}")
        return score

    @staticmethod
    def score_closed_8(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """closed_8: Pride project (count or yes/no) -> 0-2"""
        values = IndicatorScorer._get_numeric_values(row)

        if values:
            # Numeric version: count of representatives
            count = values[0]
            if count >= 1:
                score = 2.0
            else:
                score = 0.0
            logger.debug(f"closed_8: count={count}, score={score}")
            return score

        # Try да/нет
        data_cols = IndicatorScorer._get_data_columns(row)
        for col in data_cols:
            val = row[col]
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str == 'да':
                    logger.debug(f"closed_8: да -> 2.0")
                    return 2.0
                elif val_str == 'нет':
                    logger.debug(f"closed_8: нет -> 0.0")
                    return 0.0

        logger.debug(f"closed_8: No data found, returning 0.0")
        return 0.0

    # ============ PENALTY INDICATORS (pen_1 to pen_3) ============

    @staticmethod
    def score_pen_1(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_1: Regional conflicts (2 yes/no) -> -3 to +2"""
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
                        score += -3.0  # Public conflict with Governor
                    else:
                        score += -2.0  # Conflict with regional ministry
                elif val_str == 'нет':
                    score += 1.0

                count += 1

        if count == 0:
            logger.debug(f"pen_1: No да/нет values found, returning 0")
            return 0.0

        logger.debug(f"pen_1: count={count}, score={score}")
        return score

    @staticmethod
    def score_pen_2(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_2: Internal conflicts (quarterly/annual counts + media) -> -3 to +1"""
        values = IndicatorScorer._get_numeric_values(row)
        data_cols = IndicatorScorer._get_data_columns(row)

        if not values:
            logger.debug(f"pen_2: No numeric values found")
            return 0.0

        # First numeric: quarterly or annual count
        count = int(values[0])
        score = 0.0

        # Systematic conflicts (1+ per quarter or 4+ per year) -> -3
        if count >= 4 or (len(values) > 1 and values[1] >= 4):
            score = -3.0
        # Check for media mentions (да/нет)
        else:
            has_media = False
            for col in data_cols:
                val = row[col]
                if pd.notna(val):
                    val_str = str(val).strip().lower()
                    if val_str == 'да':
                        has_media = True
                        break

            if has_media:
                score = -2.0  # Media coverage -> -2
            elif count > 0:
                score = -1.0  # Some conflicts without media
            else:
                score = 1.0  # No conflicts

        logger.debug(f"pen_2: count={count}, score={score}")
        return score

    @staticmethod
    def score_pen_3(row: pd.Series, col_mapping: dict = None) -> Optional[float]:
        """pen_3: Law enforcement data (3 yes/no) -> -5 to +3"""
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
                        score += -2.0  # Law enforcement checks
                    else:
                        score += -1.0  # Media publications
                elif val_str == 'нет':
                    score += 1.0

                count += 1

        if count == 0:
            logger.debug(f"pen_3: No да/нет values found, returning 0")
            return 0.0

        logger.debug(f"pen_3: count={count}, score={score}")
        return score

    # ============ MAIN SCORING METHOD ============

    @classmethod
    def score_indicator(cls, indicator_code: str, row: pd.Series) -> Optional[float]:
        """Score any indicator"""
        scoring_func = getattr(cls, f"score_{indicator_code}", None)

        if not scoring_func:
            logger.warning(f"No scoring function for {indicator_code}")
            return 0.0

        try:
            score = scoring_func(row, {})

            if score is None:
                logger.warning(f"{indicator_code}: returned None, converting to 0.0")
                return 0.0

            logger.info(f"{indicator_code}: score = {score:.1f}")
            return score
        except Exception as e:
            logger.error(f"Error scoring {indicator_code}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0.0
