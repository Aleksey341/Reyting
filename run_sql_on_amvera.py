#!/usr/bin/env python3
"""
Execute SQL script on Amvera PostgreSQL database
This script connects to the remote Amvera database and executes load_official_data.sql
"""

import psycopg2
from psycopg2 import sql
import sys
import io
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Database connection details for Amvera
DB_CONFIG = {
    'host': 'amvera-alex1976-cnpg-gubernator1-rw',
    'port': 5432,
    'database': 'reyting-db',
    'user': 'reyting_admin',
    'password': 'Qwerty12345'
}

def load_sql_file(filename):
    """Load SQL commands from file"""
    filepath = Path(__file__).parent / filename
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def execute_sql_on_amvera(sql_content):
    """Execute SQL on Amvera database"""
    try:
        print("\n" + "=" * 80)
        print("CONNECTING TO AMVERA POSTGRESQL")
        print("=" * 80)
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        print()

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")

        # Execute SQL
        print("=" * 80)
        print("EXECUTING SQL SCRIPT")
        print("=" * 80 + "\n")

        cursor.execute(sql_content)
        conn.commit()

        print("\n✅ SQL executed successfully!\n")

        # Get summary
        cursor.execute("""
            SELECT code, COUNT(*) as count
            FROM dim_indicator i
            JOIN fact_indicator f ON i.ind_id = f.ind_id
            WHERE f.period_id = 1
            GROUP BY code
            ORDER BY code
        """)

        results = cursor.fetchall()
        print("=" * 80)
        print("VERIFICATION - Data loaded:")
        print("=" * 80)
        print(f"{'Code':<15} {'Count':<10}")
        print("-" * 80)

        total_records = 0
        for code, count in results:
            print(f"{code:<15} {count:<10}")
            total_records += count

        print("-" * 80)
        print(f"{'TOTAL':<15} {total_records:<10}")
        print("=" * 80 + "\n")

        # Check fact_summary
        cursor.execute("""
            SELECT COUNT(*) as summary_count
            FROM fact_summary
            WHERE period_id = 1
        """)
        summary_count = cursor.fetchone()[0]
        print(f"✅ fact_summary records: {summary_count}")
        print(f"✅ Expected: 20 (one per municipality)\n")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " LOADING OFFICIAL METHODOLOGY DATA ON AMVERA".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Load SQL file
    print("📂 Loading SQL script...\n")
    sql_content = load_sql_file('load_official_data.sql')
    print(f"✅ Loaded {len(sql_content)} characters of SQL\n")

    # Execute on Amvera
    success = execute_sql_on_amvera(sql_content)

    if success:
        print("=" * 80)
        print("✅ SUCCESS! Data has been loaded into Amvera database")
        print("=" * 80)
        print("\n📋 Next steps:")
        print("1. Redeploy application on Amvera (or restart it)")
        print("2. Wait for migrations to run (check logs)")
        print("3. Hard refresh Rating tab (Ctrl+F5)")
        print("4. Scores should display instead of zeros ✅\n")
    else:
        print("=" * 80)
        print("❌ FAILED! Could not execute SQL")
        print("=" * 80)
        print("\n📋 Troubleshooting:")
        print("1. Check database credentials in this script")
        print("2. Verify Amvera database is running")
        print("3. Check firewall/network connectivity")
        print("4. Try executing SQL manually in DBeaver/pgAdmin\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
