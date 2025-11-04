#!/usr/bin/env python3
"""
ETL скрипт v2 для загрузки данных оценки эффективности руководителей.

Специально подготовлен для работы с реальными данными из data_extract папки.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Папка с данными
DATA_FOLDER = Path(__file__).parent.parent.parent / "data_extract"

# Mapping реальных названий МО из CSV на наших МО
MO_MAPPING = {
    'Липецк': 'Липецк',
    'Елец': 'Елец',
    'Воловский': 'Воловский',
    'Грязянский': 'Грязянский',
    'Данковский': 'Данковский',
    'Добринский': 'Добринский',
    'Добровский': 'Добровский',
    'Долгоруковский': 'Долгоруковский',
    'Елецкий': 'Елецкий',
    'Задонский': 'Задонский',
    'Измалковский': 'Измалковский',
    'Краснинский': 'Краснинский',
    'Лебедянский': 'Лебедянский',
    'Лев-Толстовский': 'Лев-Толстовский',
    'Липецкий': 'Липецкий',
    'Становлянский': 'Становлянский',
    'Тербунский': 'Тербунский',
    'Усманский': 'Усманский',
    'Хлевенский': 'Хлевенский',
    'Чаплыгинский': 'Чаплыгинский',
}

# Mapping категорий на индикаторы
INDICATOR_MAPPING = {
    'Оценка поддержки руководства об': {'code': 'SUPPORT', 'name': 'Оценка поддержки руководства', 'weight': 0.15},
    'Выполнение задач АГП': {'code': 'AGP_TASKS', 'name': 'Выполнение задач АГП', 'weight': 0.1},
    'Позиционирование главы МО': {'code': 'POSITIONING', 'name': 'Позиционирование главы МО', 'weight': 0.05},
    'Личная работа главы с ветеранам': {'code': 'VETERANS', 'name': 'Работа с ветеранами', 'weight': 0.05},
    'Внутримуниципальные конфликты': {'code': 'CONFLICTS_INTERNAL', 'name': 'Внутримуниципальные конфликты', 'weight': 0.08},
    'Вовлеченность молодежи _Движени': {'code': 'YOUTH_FIRST', 'name': 'Вовлеченность в Движение Первых', 'weight': 0.07},
    'Вовлеченность молодежи _Добровол': {'code': 'YOUTH_VOLUNTEER', 'name': 'Добровольческая деятельность', 'weight': 0.06},
    'Данные правоохранительных орган': {'code': 'LAW_ENFORCEMENT', 'name': 'Данные правоохранительных органов', 'weight': 0.1},
    'Кадровый управленческий резерв': {'code': 'PERSONNEL_RESERVE', 'name': 'Кадровый резерв', 'weight': 0.05},
    'Конфликты с региональной власть': {'code': 'CONFLICTS_REGIONAL', 'name': 'Конфликты с региональной властью', 'weight': 0.08},
    'Партийная принадлежность ветера': {'code': 'PARTY_VETERANS', 'name': 'Партийная принадлежность ветеранов', 'weight': 0.03},
    'Партийная принадлежность сотруд': {'code': 'PARTY_STAFF', 'name': 'Партийная принадлежность сотрудников', 'weight': 0.03},
    'Показатели АГП _Качество_': {'code': 'AGP_QUALITY', 'name': 'Показатели АГП - Качество', 'weight': 0.08},
    'Показатели АГП _Уровень_': {'code': 'AGP_LEVEL', 'name': 'Показатели АГП - Уровень', 'weight': 0.07},
    'Проектная деятельность': {'code': 'PROJECT_ACTIVITY', 'name': 'Проектная деятельность', 'weight': 0.06},
    'Работа с грантами': {'code': 'GRANTS', 'name': 'Работа с грантами', 'weight': 0.07},
    'Распределение мандатов': {'code': 'MANDATES', 'name': 'Распределение мандатов', 'weight': 0.04},
    'Участие в проекте _Гордость Лип': {'code': 'PRIDE_PROJECT', 'name': 'Проект Гордость Липецка', 'weight': 0.04},
    'Экономическая привлекательность': {'code': 'ECONOMIC_ATTRACT', 'name': 'Экономическая привлекательность', 'weight': 0.05},
}

def analyze_data():
    """Анализирует структуру данных в CSV файлах."""
    logger.info("=" * 70)
    logger.info("📊 АНАЛИЗ СТРУКТУРЫ ДАННЫХ")
    logger.info("=" * 70)

    csv_files = sorted(DATA_FOLDER.glob("*.csv"))
    logger.info(f"📁 Найдено CSV файлов: {len(csv_files)}\n")

    all_data = []

    for csv_file in csv_files:
        logger.info(f"📄 {csv_file.name}")

        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            logger.info(f"   Строк: {len(df)}, Колонок: {len(df.columns)}")

            # Показываем структуру
            if len(df) > 0:
                logger.info(f"   Колонки: {', '.join(df.columns.tolist()[:5])}...")
                logger.info(f"   Пример строки:")
                first_row = df.iloc[0]
                for col in ['Лист', 'Муниципалитет', 'Глава МО']:
                    if col in df.columns:
                        logger.info(f"     - {col}: {first_row.get(col, 'N/A')}")

            all_data.append({
                'file': csv_file.name,
                'rows': len(df),
                'cols': len(df.columns),
            })

        except Exception as e:
            logger.error(f"   ✗ Ошибка: {e}")

        logger.info("")

    logger.info("=" * 70)
    logger.info(f"✅ Анализ завершен. Всего файлов: {len(all_data)}")
    logger.info("=" * 70)

    return all_data

def extract_and_convert_data():
    """Извлекает данные из CSV и преобразует их в структурированный формат."""
    logger.info("\n" + "=" * 70)
    logger.info("📊 ИЗВЛЕЧЕНИЕ И ТРАНСФОРМАЦИЯ ДАННЫХ")
    logger.info("=" * 70)

    csv_files = sorted(DATA_FOLDER.glob("*.csv"))
    extracted_data = []

    for csv_file in csv_files:
        logger.info(f"\n📄 Обработка: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')

            if df.empty or 'Муниципалитет' not in df.columns:
                logger.warning(f"   ⚠ Пропускаю - нет колонки 'Муниципалитет'")
                continue

            # Получаем категорию из первой строки (колонка 'Лист')
            category = None
            if 'Лист' in df.columns and len(df) > 0:
                category = str(df.iloc[0].get('Лист', '')).strip()

            if not category or category == 'nan' or category == '':
                category = csv_file.name.split('__')[-1].replace('.csv', '')

            logger.info(f"   Категория: {category}")

            # Обрабатываем каждую строку
            for idx, row in df.iterrows():
                try:
                    mo_name = str(row.get('Муниципалитет', '')).strip()
                    head_name = str(row.get('Глава МО', '')).strip()

                    if not mo_name or mo_name == 'nan' or mo_name == '':
                        continue

                    if mo_name not in MO_MAPPING:
                        continue

                    # Извлекаем числовые значения
                    for col in df.columns:
                        if col in ['Лист', 'Муниципалитет', 'Глава МО']:
                            continue

                        value = row.get(col)
                        if value is None or (isinstance(value, str) and value.strip() == ''):
                            continue

                        # Парсим значение
                        parsed_value = None
                        if isinstance(value, (int, float)):
                            parsed_value = float(value)
                        elif isinstance(value, str):
                            value_clean = value.strip().lower()
                            if value_clean in ['да', 'yes', 'true']:
                                parsed_value = 1.0
                            elif value_clean in ['нет', 'no', 'false']:
                                parsed_value = 0.0
                            else:
                                try:
                                    parsed_value = float(value.replace(',', '.'))
                                except:
                                    continue

                        if parsed_value is not None:
                            extracted_data.append({
                                'mo_name': mo_name,
                                'head_name': head_name,
                                'category': category,
                                'indicator_code': col[:20],  # Сокращенный код
                                'value_raw': parsed_value,
                                'filename': csv_file.name
                            })

                except Exception as e:
                    logger.debug(f"   Ошибка в строке {idx}: {e}")
                    continue

            logger.info(f"   ✓ Извлечено {sum(1 for d in extracted_data if d['mo_name'] in [x['mo_name'] for x in extracted_data[-1:]])} записей")

        except Exception as e:
            logger.error(f"   ✗ Ошибка при обработке: {e}")

    logger.info("\n" + "=" * 70)
    logger.info(f"✅ Экстракция завершена. Всего извлечено: {len(extracted_data)} записей")
    logger.info("=" * 70)

    return extracted_data

def save_extracted_data(data):
    """Сохраняет извлеченные данные в JSON для дальнейшей загрузки."""
    output_file = DATA_FOLDER.parent / "extracted_data.json"

    import json

    logger.info(f"\n💾 Сохраняю данные в: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Сохранено {len(data)} записей")

    return output_file

def main():
    """Главная функция."""
    logger.info("\n" + "=" * 70)
    logger.info("🔍 АНАЛИЗ ДАННЫХ ОЦЕНКИ ЭФФЕКТИВНОСТИ РУКОВОДИТЕЛЕЙ")
    logger.info("=" * 70)
    logger.info(f"📁 Папка с данными: {DATA_FOLDER}")

    # Проверяем что папка существует
    if not DATA_FOLDER.exists():
        logger.error(f"✗ Папка не найдена: {DATA_FOLDER}")
        return

    # Анализируем структуру
    analysis = analyze_data()

    # Извлекаем данные
    extracted = extract_and_convert_data()

    # Сохраняем данные
    if extracted:
        output_file = save_extracted_data(extracted)
        logger.info(f"\n✅ Данные готовы к загрузке!")
        logger.info(f"   Файл: {output_file}")
        logger.info(f"   Записей: {len(extracted)}")
        logger.info(f"   Период: 2024-Q4")
    else:
        logger.warning("⚠ Не удалось извлечь данные")

    logger.info("\n" + "=" * 70)
    logger.info("✅ Завершено")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
