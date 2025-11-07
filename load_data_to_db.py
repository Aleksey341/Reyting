"""
Скрипт для загрузки данных из CSV в PostgreSQL базу данных
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date
import os

# Database connection (внешний домен PostgreSQL)
DATABASE_URL = "postgresql://reyting_admin:Qwerty12345@gubernator1-alex1976.db-msk0.amvera.tech:5432/reyting-db"

# Путь к файлу
CSV_FILE = r"C:\Users\cobra\Desktop\Дашборд Липецкой области\Дашборд Губернатора главы регионов\extracted_data\Оценка_поддержки_руководителя_v1__ALL.csv"

def connect_db():
    """Подключение к БД"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("[OK] Подключение к БД успешно")
        return conn
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к БД: {e}")
        return None

def load_csv():
    """Загрузка CSV файла"""
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
        print(f"[OK] CSV загружен: {len(df)} строк, {len(df.columns)} колонок")
        return df
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки CSV: {e}")
        return None

def create_municipalities(conn, df):
    """Создание муниципалитетов в dim_mo"""
    cursor = conn.cursor()

    # Извлекаем уникальные муниципалитеты
    municipalities = df[['Муниципалитет', 'Глава МО']].drop_duplicates()

    inserted = 0
    for _, row in municipalities.iterrows():
        mo_name = row['Муниципалитет']
        if pd.isna(mo_name) or mo_name == '':
            continue

        try:
            cursor.execute("""
                INSERT INTO dim_mo (mo_name, type)
                VALUES (%s, %s)
                ON CONFLICT (mo_name) DO NOTHING
                RETURNING mo_id
            """, (mo_name, 'Муниципальный район'))

            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  Ошибка при вставке МО '{mo_name}': {e}")
            conn.rollback()
            continue

    conn.commit()
    print(f"[OK] Создано муниципалитетов: {inserted}")
    cursor.close()

def create_period(conn):
    """Создание периода 2024-01 (январь 2024)"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO dim_period (period_type, date_from, date_to, edg_flag)
            VALUES ('month', '2024-01-01', '2024-01-31', false)
            ON CONFLICT DO NOTHING
            RETURNING period_id
        """)

        if cursor.rowcount > 0:
            period_id = cursor.fetchone()[0]
            print(f"[OK] Создан период: 2024-01 (ID: {period_id})")
        else:
            cursor.execute("SELECT period_id FROM dim_period WHERE date_from = '2024-01-01'")
            period_id = cursor.fetchone()[0]
            print(f"[OK] Период уже существует: 2024-01 (ID: {period_id})")

        conn.commit()
        cursor.close()
        return period_id
    except Exception as e:
        print(f"[ERROR] Ошибка создания периода: {e}")
        conn.rollback()
        cursor.close()
        return None

def create_methodology(conn):
    """Создание версии методологии v1"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO dim_methodology (version, valid_from, notes)
            VALUES ('v1', '2024-01-01', 'Оценка поддержки руководителя v1')
            ON CONFLICT (version) DO NOTHING
            RETURNING version_id
        """)

        if cursor.rowcount > 0:
            version_id = cursor.fetchone()[0]
            print(f"[OK] Создана методология: v1 (ID: {version_id})")
        else:
            cursor.execute("SELECT version_id FROM dim_methodology WHERE version = 'v1'")
            version_id = cursor.fetchone()[0]
            print(f"[OK] Методология уже существует: v1 (ID: {version_id})")

        conn.commit()
        cursor.close()
        return version_id
    except Exception as e:
        print(f"[ERROR] Ошибка создания методологии: {e}")
        conn.rollback()
        cursor.close()
        return None

def create_indicators(conn, df):
    """Создание индикаторов в dim_indicator"""
    cursor = conn.cursor()

    # Список колонок-индикаторов (все кроме служебных)
    skip_columns = ['Лист', 'Муниципалитет', 'Глава МО']
    indicator_columns = [col for col in df.columns if col not in skip_columns]

    inserted = 0
    for col_name in indicator_columns:
        # Генерируем код индикатора из названия
        code = col_name[:50].replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')

        try:
            cursor.execute("""
                INSERT INTO dim_indicator (code, name, block, is_public)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
                RETURNING ind_id
            """, (code, col_name, 'Оценка поддержки руководителя', True))

            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  Ошибка при вставке индикатора '{col_name}': {e}")
            conn.rollback()
            continue

    conn.commit()
    print(f"[OK] Создано индикаторов: {inserted}")
    cursor.close()

def load_indicator_values(conn, df, period_id, version_id):
    """Загрузка значений индикаторов в fact_indicator"""
    cursor = conn.cursor()

    # Получаем мапинг МО
    cursor.execute("SELECT mo_id, mo_name FROM dim_mo")
    mo_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Получаем мапинг индикаторов
    cursor.execute("SELECT ind_id, code, name FROM dim_indicator")
    ind_map = {}
    for row in cursor.fetchall():
        ind_id, code, name = row
        ind_map[name] = ind_id

    # Список служебных колонок
    skip_columns = ['Лист', 'Муниципалитет', 'Глава МО']

    inserted = 0
    errors = 0

    for _, row in df.iterrows():
        mo_name = row['Муниципалитет']
        if pd.isna(mo_name) or mo_name == '' or mo_name not in mo_map:
            continue

        mo_id = mo_map[mo_name]

        for col_name in df.columns:
            if col_name in skip_columns:
                continue

            value = row[col_name]
            if pd.isna(value) or value == '':
                continue

            # Получаем ind_id
            if col_name not in ind_map:
                continue

            ind_id = ind_map[col_name]

            # Пытаемся преобразовать значение в число
            try:
                if isinstance(value, str):
                    # Убираем % и пробелы
                    value_clean = value.replace('%', '').replace(' ', '').replace(',', '.')
                    # Проверяем что это число
                    try:
                        value_raw = float(value_clean)
                    except:
                        # Если не число, сохраняем как 1 (факт присутствия)
                        value_raw = 1.0
                else:
                    value_raw = float(value)
            except:
                value_raw = 1.0

            try:
                cursor.execute("""
                    INSERT INTO fact_indicator (mo_id, period_id, ind_id, version_id, value_raw)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (mo_id, period_id, ind_id, version_id) DO UPDATE
                    SET value_raw = EXCLUDED.value_raw,
                        updated_at = NOW()
                """, (mo_id, period_id, ind_id, version_id, value_raw))

                inserted += 1
            except Exception as e:
                errors += 1
                if errors < 10:  # Показываем только первые 10 ошибок
                    print(f"  Ошибка вставки значения для {mo_name}/{col_name}: {e}")
                conn.rollback()
                continue

    conn.commit()
    print(f"[OK] Загружено значений индикаторов: {inserted}")
    if errors > 0:
        print(f"[WARN] Ошибок при загрузке: {errors}")
    cursor.close()

def main():
    """Главная функция"""
    print("=" * 60)
    print("Загрузка данных в PostgreSQL")
    print("=" * 60)

    # Подключение к БД
    conn = connect_db()
    if not conn:
        return

    # Загрузка CSV
    df = load_csv()
    if df is None:
        conn.close()
        return

    print(f"\nПервые строки данных:")
    print(df[['Муниципалитет', 'Глава МО']].head())
    print()

    # Создание справочников
    print("Шаг 1: Создание муниципалитетов...")
    create_municipalities(conn, df)

    print("\nШаг 2: Создание периода...")
    period_id = create_period(conn)
    if not period_id:
        conn.close()
        return

    print("\nШаг 3: Создание методологии...")
    version_id = create_methodology(conn)
    if not version_id:
        conn.close()
        return

    print("\nШаг 4: Создание индикаторов...")
    create_indicators(conn, df)

    print("\nШаг 5: Загрузка значений индикаторов...")
    load_indicator_values(conn, df, period_id, version_id)

    conn.close()
    print("\n" + "=" * 60)
    print("[OK] Загрузка завершена!")
    print("=" * 60)

if __name__ == "__main__":
    main()
