#!/usr/bin/env python3
"""
Indicator Scoring Logic

Converts raw Excel data into numeric scores for each official methodology indicator.
Handles different data types: numeric, categorical, and multi-column aggregation.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class IndicatorScorer:
    """Calculates indicator scores based on official methodology rules."""

    # Mapping from sheet name to indicator code
    SHEET_TO_CODE = {
        # PUBLIC CRITERIA (pub_1 to pub_9)
        "Оценка поддержки руководства об": "pub_1",
        "Выполнение задач АГП": "pub_2",
        "Позиционирование главы МО": "pub_3",
        "Проектная деятельность": "pub_4",
        "Вовлеченность молодежи (Доброво": "pub_5",
        "Вовлеченность молодежи (Движени": "pub_6",
        "Личная работа главы с ветеранам": "pub_7",
        "Кадровый управленческий резерв": "pub_8",
        "Работа с грантами": "pub_9",

        # CLOSED CRITERIA (closed_1 to closed_8)
        "Партийная принадлежность сотруд": "closed_1",
        "Распределение мандатов": "closed_2",
        "Показатели АГП (Уровень)": "closed_3",
        "Показатели АГП (Качество)": "closed_4",
        "Экономическая привлекательность": "closed_5",
        "Партийная принадлежность ветера": "closed_7",
        "Участие в проекте «Гордость Лип": "closed_8",

        # PENALTY CRITERIA (pen_1 to pen_3)
        "Конфликты с региональной власть": "pen_1",
        "Внутримуниципальные конфликты": "pen_2",
        "Данные правоохранительных орган": "pen_3",
    }

    @staticmethod
    def score_pub_1(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_1: Поддержка руководства области

        Многостолбцовый показатель:
        - Факт публичной поддержки (Да=1, Нет=0)
        - Факт поддержки с первым заместителем (Да=1, Нет=0)
        - Факт поддержки со стороны ключевых руководителей (Да=1, Нет=0)

        Результат: сумма (0-3)
        """
        score = 0.0

        # Identify columns for pub_1 (3 да/нет questions)
        # Skip municipality and head name columns
        skip_cols = ['муниципалитет', 'глава', 'мо', 'fio', 'name']
        da_net_cols = [col for col in row.index
                      if col.lower() not in skip_cols
                      and pd.notna(row[col])
                      and isinstance(row[col], str)
                      and row[col].strip().lower() in ['да', 'нет']]

        logger.debug(f"pub_1: Found {len(da_net_cols)} да/нет columns: {da_net_cols}")

        if len(da_net_cols) < 3:
            logger.debug(f"pub_1: Not enough да/нет columns ({len(da_net_cols)}), expected 3")
            return None

        # Take first 3 да/нет columns (in order they appear)
        for col in da_net_cols[:3]:
            if pd.notna(row[col]):
                value = str(row[col]).strip().lower()
                score += 1.0 if value == 'да' else 0.0

        logger.debug(f"pub_1: Calculated score = {score}")
        return min(score, 3.0)

    @staticmethod
    def score_pub_2(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_2: Выполнение задач АГП

        Простой числовой показатель (%):
        - Процент выполнения задач АГП (0.0-1.0 или 0-100%)

        Нормализация: значение * 5 (на шкалу 0-5)
        """
        # Find numeric column (not МО name or Глава МО)
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    # Assume value is in 0-1 range (95% = 0.95)
                    # If > 1, assume it's in percentage (95 = 95%)
                    if value > 1:
                        value = value / 100
                    return min(value * 5, 5.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pub_3(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_3: Позиционирование главы МО

        Категориальный показатель (текст):
        - "функционер" или "хозяйственник" → 3 балла
        - "размытое" или "некачественное" → 0 баллов
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if 'функционер' in value or 'хозяйственник' in value:
                    return 3.0
                elif 'размытое' in value or 'некачественное' in value:
                    return 0.0

        return None

    @staticmethod
    def score_pub_4(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_4: Проектная деятельность главы

        Числовой показатель (количество проектов):
        - Нормализация: MIN(проекты / 2, 3)
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    return min(value / 2, 3.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pub_5(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_5: Молодежь в добровольчестве

        Числовой показатель (%):
        - Нормализация: значение * 3
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    if value > 1:
                        value = value / 100
                    return min(value * 3, 3.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pub_6(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_6: Молодежь в Движении Первых

        Числовой показатель (количество членов):
        - Нормализация: MIN(члены / 100, 3)
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    return min(value / 100, 3.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pub_7(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_7: Работа с ветеранами СВО (публичная)

        Многостолбцовый показатель:
        - Количество встреч (число) → встречи/20, макс 1.0
        - % участия главы (%) → значение * 1
        - % решенных обращений (%) → значение * 1

        Результат: встречи + участие + решение (0-3)
        """
        numeric_cols = []
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    numeric_cols.append(value)
                except (ValueError, TypeError):
                    continue

        if len(numeric_cols) < 3:
            return None

        # First numeric = количество встреч
        # Second numeric = % участия
        # Third numeric = % решений

        meet_score = min(numeric_cols[0] / 20, 1.0)  # Max 20 встреч = 1.0 балл

        # For percentages, normalize to 0-1
        particip = numeric_cols[1]
        if particip > 1:
            particip = particip / 100
        particip_score = min(particip * 1, 1.0)

        solution = numeric_cols[2]
        if solution > 1:
            solution = solution / 100
        solution_score = min(solution * 1, 1.0)

        return min(meet_score + particip_score + solution_score, 3.0)

    @staticmethod
    def score_pub_8(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_8: Кадровый управленческий резерв

        Числовой показатель (количество в резерве):
        - Нормализация: MIN(резерв / 5, 3)
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    return min(value / 5, 3.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pub_9(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pub_9: Работа с грантами

        Многостолбцовый показатель:
        - Количество побед в грантах (число) → побед/3, макс 1.5
        - Объем привлеченных средств (млн) → объем/100 * 1.5, макс 1.5
        - Нарушений (Да/Нет) → Нет=1, Да=-2

        Результат: MAX(0, побед + объем + нарушения) (0-3)
        """
        score = 0.0
        numeric_count = 0

        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value_str = str(row[col]).strip()

                # Check for да/нет
                if value_str.lower() in ['да', 'нет']:
                    violations = 1.0 if value_str.lower() == 'нет' else -2.0
                    score += violations
                else:
                    # Try numeric
                    try:
                        value = float(value_str)
                        if numeric_count == 0:
                            # First numeric: количество побед
                            score += min(value / 3, 1.5)
                        elif numeric_count == 1:
                            # Second numeric: объем в млн
                            # Skip dates (if value looks like a date)
                            if value < 5000:  # Reasonable range for млн
                                score += min(value / 100 * 1.5, 1.5)
                        numeric_count += 1
                    except (ValueError, TypeError):
                        # Skip non-numeric
                        pass

        return max(min(score, 3.0), 0.0)

    @staticmethod
    def score_closed_1(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_1: Партийное мнение в администрации

        Многостолбцовый показатель (3 метрики):
        - Общее число сотрудников (число) → пропустить
        - % членов партии (%) → % * 3
        - % сторонников партии (%) → % * 3

        Результат: MIN(члены + сторонники, 6) (0-6)
        """
        score = 0.0
        numeric_count = 0

        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])

                    if numeric_count == 0:
                        # First numeric: total employees (skip)
                        pass
                    elif numeric_count == 1:
                        # Second: % members
                        if value > 1:
                            value = value / 100
                        score += min(value * 3, 3.0)
                    elif numeric_count == 2:
                        # Third: % supporters
                        if value > 1:
                            value = value / 100
                        score += min(value * 3, 3.0)

                    numeric_count += 1
                except (ValueError, TypeError):
                    continue

        return min(score, 6.0)

    @staticmethod
    def score_closed_2(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_2: Альтернативное мнение в органе

        Числовой показатель (%):
        - Нормализация: значение * 4
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    if value > 1:
                        value = value / 100
                    return min(value * 4, 4.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_closed_3(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_3: Целевые показатели АГП (уровень)

        Категориальный показатель (текст):
        - "превысил" → 5
        - "выполнен" → 3
        - "не выполнен" или "не достигнут" → 0
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if 'превысил' in value:
                    return 5.0
                elif 'выполнен' in value and 'не' not in value:
                    return 3.0
                elif 'не выполнен' in value or 'не достигнут' in value:
                    return 0.0

        return None

    @staticmethod
    def score_closed_4(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_4: Целевые показатели АГП (качество)

        Категориальный показатель (текст):
        - "превышает" → 5
        - "достигнут" → 3
        - "не достигнут" или "не выполнен" → 0
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if 'превышает' in value or 'превышен' in value:
                    return 5.0
                elif 'достигнут' in value and 'не' not in value:
                    return 3.0
                elif 'не достигнут' in value or 'не выполнен' in value:
                    return 0.0

        return None

    @staticmethod
    def score_closed_5(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_5: Экономическая привлекательность МО

        Категориальный показатель (текст):
        - "высокая" → 3
        - "средняя" → 2
        - "низкая" или "слабая" → 1
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if 'высокая' in value:
                    return 3.0
                elif 'средняя' in value:
                    return 2.0
                elif 'низкая' in value or 'слабая' in value:
                    return 1.0

        return None

    @staticmethod
    def score_closed_7(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_7: Политическая деятельность ветеранов

        Числовой показатель (%):
        - Нормализация: значение * 6
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                try:
                    value = float(row[col])
                    if value > 1:
                        value = value / 100
                    return min(value * 6, 6.0)
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_closed_8(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        closed_8: Проект "Гордость Липецкой земли"

        Может быть категориальным (Да/Нет) или числовым (количество):
        - Да → 3, Нет → 0
        - Количество → MIN(количество / 5, 3)
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip()

                # Check for да/нет
                if value.lower() == 'да':
                    return 3.0
                elif value.lower() == 'нет':
                    return 0.0

                # Try numeric
                try:
                    num_value = float(value)
                    return min(num_value / 5, 3.0)
                except (ValueError, TypeError):
                    pass

        return None

    @staticmethod
    def score_pen_1(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pen_1: Конфликты с региональной властью

        Многостолбцовый показатель (2 факта Да/Нет):
        - Публичный конфликт (Да=-3, Нет=1)
        - Конфликт с профильным заместителем (Да=-2, Нет=1)

        Результат: сумма (-5 до 2)
        """
        score = 0.0
        da_net_count = 0

        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if value in ['да', 'нет']:
                    if da_net_count == 0:
                        # Публичный конфликт
                        score += -3.0 if value == 'да' else 1.0
                    elif da_net_count == 1:
                        # Конфликт с профильным
                        score += -2.0 if value == 'да' else 1.0

                    da_net_count += 1
                    if da_net_count >= 2:
                        break

        if da_net_count < 2:
            return None

        return score

    @staticmethod
    def score_pen_2(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pen_2: Внутримуниципальные конфликты

        Многостолбцовый показатель (количество конфликтов):
        - 1+ в квартал → -3
        - 1+ в год → -2
        - 0 конфликтов → 1
        """
        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                # Check for text markers
                if 'квартал' in value:
                    if any(x in value for x in ['1', '+', 'более']):
                        return -3.0
                elif 'год' in value or 'annual' in value:
                    if any(x in value for x in ['1', '+', 'более']):
                        return -2.0

                # Try numeric
                try:
                    count = float(value)
                    if count >= 1:
                        return -2.0  # Default: -2 per year
                    else:
                        return 1.0
                except (ValueError, TypeError):
                    continue

        return None

    @staticmethod
    def score_pen_3(row: pd.Series, col_mapping: Dict[str, str]) -> Optional[float]:
        """
        pen_3: Данные правоохранительных органов

        Многостолбцовый показатель (3 факта Да/Нет):
        - Возбуждение уголовного дела (Да=-5, Нет=1)
        - Проверки силовых структур (Да=-2, Нет=1)
        - Публикации (Да=-1, Нет=1)

        Результат: сумма (-8 до 3)
        """
        score = 0.0
        da_net_count = 0

        for col in row.index:
            if pd.notna(row[col]) and col not in ['Муниципалитет', 'Глава МО']:
                value = str(row[col]).strip().lower()

                if value in ['да', 'нет']:
                    if da_net_count == 0:
                        # Возбуждение дела
                        score += -5.0 if value == 'да' else 1.0
                    elif da_net_count == 1:
                        # Проверки силовых
                        score += -2.0 if value == 'да' else 1.0
                    elif da_net_count == 2:
                        # Публикации
                        score += -1.0 if value == 'да' else 1.0

                    da_net_count += 1
                    if da_net_count >= 3:
                        break

        if da_net_count < 3:
            return None

        return score

    @classmethod
    def score_indicator(cls, indicator_code: str, row: pd.Series) -> Optional[float]:
        """
        Main method to score any indicator.

        Args:
            indicator_code: pub_1, pub_2, ..., pen_3
            row: pandas Series with row data

        Returns:
            Score (float) or None if cannot calculate
        """
        scoring_func = getattr(cls, f"score_{indicator_code}", None)

        if not scoring_func:
            logger.warning(f"No scoring function for {indicator_code}")
            return None

        try:
            logger.debug(f"Scoring {indicator_code}, row columns: {list(row.index)}")
            score = scoring_func(row, {})

            if score is not None:
                logger.info(f"{indicator_code}: score = {score}")
            else:
                logger.debug(f"{indicator_code}: could not calculate score (returned None)")

            return score
        except Exception as e:
            logger.error(f"Error scoring {indicator_code}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
