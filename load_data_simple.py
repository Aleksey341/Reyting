#!/usr/bin/env python3
"""Simple CSV loader with flexible filename matching"""

import csv
import sys
import io
from pathlib import Path

# Force UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapping from keywords to criterion codes
MAPPING = {
    "Выполнение задач АГП": "pub_2",
    "Поддержки руководства": "pub_1",  # "Оценка поддержки руководства"
    "Позиционирование": "pub_3",
    "Проектная деятельность": "pub_4",
    "Вовлеченность молодежи _Доброво": "pub_5",  # "Вовлеченность молодежи (Добровольчество)"
    "Вовлеченность молодежи _Движени": "pub_6",  # "Вовлеченность молодежи (Движение Первых)"
    "Личная работа главы с ветеранам": "pub_7",
    "Кадровый управленческий резерв": "pub_8",
    "Работа с грантами": "pub_9",
    "Партийная принадлежность сотруд": "closed_1",
    "Распределение мандатов": "closed_2",
    "Показатели АГП _Уровень": "closed_3",
    "Показатели АГП _Качество": "closed_4",
    "Экономическая привлекательность": "closed_5",
    "Партийная принадлежность ветера": "closed_7",
    "Участие в проекте _Гордость Лип": "closed_8",
    "Конфликты с региональной власть": "pen_1",
    "Внутримуниципальные конфликты": "pen_2",
    "Данные правоохранительных орган": "pen_3",
}

def load_all_csv():
    """Load all CSV files and print data"""
    data_dir = Path("C:/Users/cobra/Desktop/Дашборд Липецкой области/Дашборд Губернатора главы регионов/data_extract")

    print("\n" + "=" * 100)
    print("FINDING CSV FILES AND MAPPING TO OFFICIAL CRITERIA")
    print("=" * 100 + "\n")

    csv_files = sorted(data_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files\n")

    all_data = {}

    for csv_file in csv_files:
        filename = csv_file.name
        print(f"Processing: {filename}")

        # Find matching code
        code = None
        for keyword, crit_code in MAPPING.items():
            if keyword in filename:
                code = crit_code
                break

        if not code:
            print(f"  -> NOT MAPPED\n")
            continue

        # Read CSV
        try:
            records = []
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Муниципалитет'):
                        # Get score column (not MO name or leader name)
                        cols = [k for k in row.keys() if k not in ('Муниципалитет', 'Глава МО', None, '')]
                        if cols:
                            score_val = row[cols[0]]
                            records.append({
                                'mo': row['Муниципалитет'],
                                'leader': row.get('Глава МО', ''),
                                'score': score_val
                            })

            if records:
                all_data[code] = records
                print(f"  -> {code} ({len(records)} records)")
                # Print first 3 records
                for i, rec in enumerate(records[:3]):
                    print(f"     {i+1}. {rec['mo']}: {rec['score']}")
                if len(records) > 3:
                    print(f"     ... and {len(records)-3} more")
            else:
                print(f"  -> NO DATA\n")

        except Exception as e:
            print(f"  -> ERROR: {e}\n")
            continue

        print()

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    for code in sorted(all_data.keys()):
        count = len(all_data[code])
        print(f"  {code}: {count} records")

    return all_data

if __name__ == '__main__':
    data = load_all_csv()
