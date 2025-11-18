#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for IndicatorScorer

Tests the scoring logic with sample data from CSV files
"""

import sys
import pandas as pd
from pathlib import Path
import io
import locale

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from indicator_scoring import IndicatorScorer

def test_pub_1():
    """Test pub_1: Podderzhka rukovodstva (3 yes/no values)"""
    print("\n=== Testing pub_1 ===")

    # Create test rows
    test_cases = [
        {
            "Муниципалитет": "Lipetsk",
            "Глава МО": "Chentsov",
            "Публичная поддержка": "Да",
            "Первый заместитель": "Да",
            "Ключевые руководители": "Да",
            "expected": 3.0
        },
        {
            "Муниципалитет": "Elets",
            "Глава МО": "Zhabin",
            "Публичная поддержка": "Да",
            "Первый заместитель": "Да",
            "Ключевые руководители": "Нет",
            "expected": 2.0
        },
        {
            "Муниципалитет": "Volovskiy",
            "Глава МО": "Shcheglov",
            "Публичная поддержка": "Да",
            "Первый заместитель": "Нет",
            "Ключевые руководители": "Да",
            "expected": 2.0
        },
    ]

    for tc in test_cases:
        expected = tc.pop("expected")
        row = pd.Series(tc)
        score = IndicatorScorer.score_pub_1(row, {})
        status = "[PASS]" if score == expected else "[FAIL]"
        print("  {} {}: {} (expected {})".format(status, tc['Муниципалитет'], score, expected))


def test_pub_2():
    """Test pub_2: Выполнение задач АГП (numeric %)"""
    print("\n=== Testing pub_2: Выполнение задач АГП ===")

    test_cases = [
        {"value": 0.95, "expected": 4.75},
        {"value": 0.88, "expected": 4.4},
        {"value": 0.76, "expected": 3.8},
    ]

    for tc in test_cases:
        row = pd.Series({
            "Муниципалитет": "Test",
            "Глава МО": "Test",
            "% выполнения": tc["value"],
            "expected": tc["expected"]
        })
        expected = tc["expected"]
        score = IndicatorScorer.score_pub_2(row, {})
        status = "✓" if score == expected else "✗"
        print(f"{status} {tc['value']}: {score} (expected {expected})")


def test_pub_3():
    """Test pub_3: Позиционирование главы (categorical)"""
    print("\n=== Testing pub_3: Позиционирование главы ===")

    test_cases = [
        {"value": "глава-функционер/хозяйственник", "expected": 3.0},
        {"value": "размытое", "expected": 0.0},
    ]

    for tc in test_cases:
        row = pd.Series({
            "Муниципалитет": "Test",
            "Глава МО": "Test",
            "Тип позиционирования": tc["value"]
        })
        expected = tc["expected"]
        score = IndicatorScorer.score_pub_3(row, {})
        status = "✓" if score == expected else "✗"
        print(f"{status} '{tc['value']}': {score} (expected {expected})")


def test_pub_7():
    """Test pub_7: Работа с ветеранами (multi-column numeric)"""
    print("\n=== Testing pub_7: Работа с ветеранами ===")

    # 40 встреч, 0.85 участия, 0.75 решений
    # meet = 40/20 = 2.0 (max 1.0) = 1.0
    # particip = 0.85 * 1 = 0.85
    # solution = 0.75 * 1 = 0.75
    # total = 1.0 + 0.85 + 0.75 = 2.6

    row = pd.Series({
        "Муниципалитет": "Липецк",
        "Глава МО": "Ченцов Р.И.",
        "Встречи": 40,
        "Участие": 0.85,
        "Решения": 0.75
    })

    score = IndicatorScorer.score_pub_7(row, {})
    expected = 2.6
    # Allow small float differences
    status = "✓" if abs(score - expected) < 0.01 else "✗"
    print(f"{status} Липецк: {score:.2f} (expected {expected})")


def test_pen_1():
    """Test pen_1: Конфликты (2 да/нет)"""
    print("\n=== Testing pen_1: Конфликты с региональной властью ===")

    test_cases = [
        {
            "публичный": "Нет",
            "профильный": "Нет",
            "expected": 2.0  # 1 + 1
        },
        {
            "публичный": "Нет",
            "профильный": "Да",
            "expected": -1.0  # 1 + (-2)
        },
        {
            "публичный": "Да",
            "профильный": "Да",
            "expected": -5.0  # (-3) + (-2)
        },
    ]

    for tc in test_cases:
        expected = tc.pop("expected")
        row = pd.Series({
            "Муниципалитет": "Test",
            "Глава МО": "Test",
            "Публичный конфликт": tc["публичный"],
            "Профильный конфликт": tc["профильный"]
        })
        score = IndicatorScorer.score_pen_1(row, {})
        status = "✓" if score == expected else "✗"
        print(f"{status} ({tc['публичный']}, {tc['профильный']}): {score} (expected {expected})")


def test_with_real_data():
    """Test with real CSV data"""
    print("\n=== Testing with Real CSV Data ===")

    data_dir = Path("C:/Users/cobra/Desktop/Дашборд Липецкой области/Дашборд Губернатора главы регионов/data_extract")

    # Test pub_1 with real data
    csv_file = data_dir / "Оценка_поддержки_руководителя_v1__Оценка поддержки руководства об.csv"
    if csv_file.exists():
        print(f"\n** Testing pub_1 with {csv_file.name} **")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"Columns: {list(df.columns)}")
        print(f"First row:\n{df.iloc[0]}")

        score = IndicatorScorer.score_pub_1(df.iloc[0], {})
        print(f"pub_1 score for {df.iloc[0]['Муниципалитет']}: {score}")

    # Test pub_2 with real data
    csv_file = data_dir / "Оценка_поддержки_руководителя_v1__Выполнение задач АГП.csv"
    if csv_file.exists():
        print(f"\n** Testing pub_2 with {csv_file.name} **")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"Columns: {list(df.columns)}")
        print(f"First row:\n{df.iloc[0]}")

        score = IndicatorScorer.score_pub_2(df.iloc[0], {})
        print(f"pub_2 score for {df.iloc[0]['Муниципалитет']}: {score}")

    # Test pub_7 with real data
    csv_file = data_dir / "Оценка_поддержки_руководителя_v1__Личная работа главы с ветеранам.csv"
    if csv_file.exists():
        print(f"\n** Testing pub_7 with {csv_file.name} **")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"Columns: {list(df.columns)}")
        print(f"First row:\n{df.iloc[0]}")

        score = IndicatorScorer.score_pub_7(df.iloc[0], {})
        print(f"pub_7 score for {df.iloc[0]['Муниципалитет']}: {score}")


if __name__ == "__main__":
    print("=" * 60)
    print("INDICATOR SCORING TESTS")
    print("=" * 60)

    test_pub_1()
    test_pub_2()
    test_pub_3()
    test_pub_7()
    test_pen_1()

    test_with_real_data()

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
