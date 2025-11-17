#!/usr/bin/env python3
"""
Load CSV data with official methodology codes.

Maps criterion names from CSV files to official methodology codes:
- pub_1 to pub_9 (PUBLIC)
- closed_1 to closed_8 (CLOSED)
- pen_1 to pen_3 (PENALTIES)
"""

import csv
import os
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapping from CSV criterion names to official codes
CRITERIA_MAPPING = {
    # PUBLIC (ПУБЛИЧНЫЙ) - 9 criteria
    "Оценка поддержки руководства области": "pub_1",
    "Выполнение задач АГП": "pub_2",
    "Позиционирование главы МО": "pub_3",
    "Позиционирование главы": "pub_3",
    "Проектная деятельность": "pub_4",
    "Вовлеченность молодежи (Добровольчество)": "pub_5",
    "Вовлеченность молодежи _Доброво": "pub_5",
    "Молодежь в добровольчестве": "pub_5",
    "Вовлеченность молодежи (Движение Первых)": "pub_6",
    "Вовлеченность молодежи _Движени": "pub_6",
    "Молодежь в Движении Первых": "pub_6",
    "Личная работа главы с ветеранами СВО": "pub_7",
    "Личная работа главы с ветеранам": "pub_7",
    "Кадровый управленческий резерв": "pub_8",
    "Кадровый резерв": "pub_8",
    "Работа с грантами": "pub_9",

    # CLOSED (ЗАКРЫТЫЙ) - 8 criteria
    "Партийная принадлежность сотрудников администрации": "closed_1",
    "Партийная принадлежность сотруд": "closed_1",
    "Партийное мнение в администрации": "closed_1",
    "Распределение мандатов": "closed_2",
    "Распределение мандатов в представительном органе": "closed_2",
    "Альтернативное мнение в органе": "closed_2",
    "Показатели АГП (Уровень)": "closed_3",
    "Показатели АГП _Уровень": "closed_3",
    "Целевые показатели АГП (уровень)": "closed_3",
    "Показатели АГП (Качество)": "closed_4",
    "Показатели АГП _Качество": "closed_4",
    "Целевые показатели АГП (качество)": "closed_4",
    "Экономическая привлекательность": "closed_5",
    "Экономическая привлекательность МО": "closed_5",
    "Партийная принадлежность ветеранов": "closed_7",
    "Партийная принадлежность ветера": "closed_7",
    "Участие в проекте (Гордость Липецкой земли)": "closed_8",
    "Участие в проекте _Гордость Лип": "closed_8",
    "Проект Гордость Липецкой земли": "closed_8",

    # PENALTIES (ШТРАФЫ) - 3 criteria
    "Конфликты с региональной властью": "pen_1",
    "Конфликты с региональной власть": "pen_1",
    "Внутримуниципальные конфликты": "pen_2",
    "Правоохранительные органы": "pen_3",
    "Данные правоохранительных органов": "pen_3",
    "Данные правоохранительных орган": "pen_3",
}

def load_csv_data(data_dir: Path) -> Dict[str, List[Dict]]:
    """
    Load all CSV files and group by criterion code.

    Args:
        data_dir: Directory containing CSV files

    Returns:
        Dictionary mapping criterion code to list of records
    """
    all_data = {}

    print("\n" + "=" * 80)
    print("LOADING CSV DATA FOR OFFICIAL METHODOLOGY")
    print("=" * 80)

    csv_files = sorted([f for f in data_dir.glob("*.csv") if f.is_file()])
    print(f"\nFound {len(csv_files)} CSV files\n")

    for csv_file in csv_files:
        filename = csv_file.name

        # Extract criterion name from filename
        # Format: Оценка_поддержки_руководителя_v1__<criterion_name>.csv
        parts = filename.replace("Оценка_поддержки_руководителя_v1__", "").replace(".csv", "")
        parts = parts.rstrip(".")

        # Find matching code
        code = None
        for criterion_name, criterion_code in CRITERIA_MAPPING.items():
            if criterion_name in parts or parts in criterion_name:
                code = criterion_code
                break

        if not code:
            print(f"⚠️  SKIPPED: {parts} (no matching code)")
            continue

        # Read CSV file
        try:
            records = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Муниципалитет'):  # Skip empty rows
                        records.append({
                            'mo_name': row['Муниципалитет'],
                            'leader_name': row.get('Глава МО', ''),
                            'score': row[[k for k in row.keys() if k not in ('Муниципалитет', 'Глава МО')][0]]
                        })

            if records:
                all_data[code] = records
                print(f"✓ {code}: {parts} ({len(records)} records)")
            else:
                print(f"⚠️  EMPTY: {parts}")

        except Exception as e:
            print(f"✗ ERROR reading {csv_file.name}: {e}")

    print("\n" + "=" * 80)
    print("MAPPING SUMMARY")
    print("=" * 80)

    public_criteria = {k: v for k, v in all_data.items() if k.startswith('pub_')}
    closed_criteria = {k: v for k, v in all_data.items() if k.startswith('closed_')}
    penalty_criteria = {k: v for k, v in all_data.items() if k.startswith('pen_')}

    print(f"\nПУБЛИЧНЫЙ: {len(public_criteria)}/9 criteria loaded")
    for code in sorted(public_criteria.keys()):
        print(f"  ✓ {code}")

    missing_public = [f"pub_{i}" for i in range(1, 10) if f"pub_{i}" not in all_data]
    if missing_public:
        print(f"  ✗ Missing: {', '.join(missing_public)}")

    print(f"\nЗАКРЫТЫЙ: {len(closed_criteria)}/8 criteria loaded")
    for code in sorted(closed_criteria.keys()):
        print(f"  ✓ {code}")

    missing_closed = [f"closed_{i}" for i in range(1, 9) if f"closed_{i}" not in all_data]
    if missing_closed:
        print(f"  ✗ Missing: {', '.join(missing_closed)}")

    print(f"\nШТРАФНЫЕ: {len(penalty_criteria)}/3 criteria loaded")
    for code in sorted(penalty_criteria.keys()):
        print(f"  ✓ {code}")

    missing_penalties = [f"pen_{i}" for i in range(1, 4) if f"pen_{i}" not in all_data]
    if missing_penalties:
        print(f"  ✗ Missing: {', '.join(missing_penalties)}")

    return all_data


def generate_sql_inserts(data: Dict[str, List[Dict]]) -> str:
    """
    Generate SQL INSERT statements for fact_indicator table.

    Args:
        data: Dictionary mapping criterion code to records

    Returns:
        SQL INSERT statements
    """
    sql_lines = []

    # Get current period ID (assuming latest period)
    period_id = 1  # Change based on your period ID

    for code, records in sorted(data.items()):
        print(f"\nProcessing {code} ({len(records)} records)...")

        for record in records:
            mo_name = record['mo_name'].strip()
            score_str = record['score'].strip().replace(',', '.')

            try:
                score = float(score_str)
            except ValueError:
                print(f"  ⚠️  Skipped {mo_name}: invalid score '{score_str}'")
                continue

            sql_lines.append(f"""
-- {mo_name} -> {code}
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT
    m.mo_id,
    i.ind_id,
    {period_id},
    {score},
    NOW(),
    NOW()
FROM dim_mo m, dim_indicator i
WHERE m.mo_name = '{mo_name}'
    AND i.code = '{code}'
    AND NOT EXISTS (
        SELECT 1 FROM fact_indicator f
        WHERE f.mo_id = m.mo_id
        AND f.ind_id = i.ind_id
        AND f.period_id = {period_id}
    );
""")

    return "\n".join(sql_lines)


def main():
    data_dir = Path("C:/Users/cobra/Desktop/Дашборд Липецкой области/Дашборд Губернатора главы регионов/data_extract")

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return

    # Load CSV data
    data = load_csv_data(data_dir)

    # Generate SQL
    sql = generate_sql_inserts(data)

    # Save SQL to file
    output_file = Path("load_methodology_data.sql")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- SQL to load CSV data into fact_indicator with official methodology codes\n")
        f.write("-- IMPORTANT: Adjust period_id as needed\n\n")
        f.write(sql)

    print("\n" + "=" * 80)
    print(f"SQL file generated: {output_file.absolute()}")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Edit load_methodology_data.sql and adjust period_id if needed")
    print("2. Run SQL against Amvera PostgreSQL database")
    print("3. Refresh Rating page in frontend")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
