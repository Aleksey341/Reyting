#!/bin/bash

# Complete Amvera Migration Script
# Applies both column addition and leader name population
# Usage: ./complete_amvera_migration.sh [password]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# DB Parameters
DB_HOST="amvera-alex1976-cnpq-reyting-mo-rw"
DB_PORT="5432"
DB_NAME="reytingdb"
DB_USER="reyting_user"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Complete Amvera Migration: Column + Leader Names${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Get password
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: password not provided${NC}"
    echo ""
    echo "Usage: $0 <password>"
    echo ""
    echo "Example:"
    echo "  $0 'my_password'"
    echo ""
    exit 1
fi

DB_PASSWORD="$1"

# Test connection
echo -e "${YELLOW}📡 Testing database connection...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to database${NC}"
    echo -e "${RED}Check connection parameters:${NC}"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔄 Starting migration...${NC}"
echo ""

# Step 1: Add column
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 1/2: Adding leader_name column...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);" 2>&1 | grep -v "^$"

PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "CREATE INDEX IF NOT EXISTS idx_dim_mo_leader_name ON dim_mo(leader_name);" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}✅ Column added successfully${NC}"
echo ""

# Step 2: Populate leader names
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 2/2: Populating leader names...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create SQL file with all updates
cat > /tmp/update_leaders.sql << 'EOSQL'
BEGIN;

UPDATE dim_mo SET leader_name = 'Ченцов Р.И.' WHERE mo_name LIKE '%Липецк%' AND mo_name NOT LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Жабин В.П.' WHERE mo_name LIKE '%Елец%' AND mo_name NOT LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щеглов С.С.' WHERE mo_name LIKE '%Воловский%';
UPDATE dim_mo SET leader_name = 'Рощупкин В.Т.' WHERE mo_name LIKE '%Грязянский%';
UPDATE dim_mo SET leader_name = 'Фалеев В.И.' WHERE mo_name LIKE '%Данковский%';
UPDATE dim_mo SET leader_name = 'Пасынков А.Н.' WHERE mo_name LIKE '%Добринский%';
UPDATE dim_mo SET leader_name = 'Попов А.А.' WHERE mo_name LIKE '%Добровский%';
UPDATE dim_mo SET leader_name = 'Тимохин А.Н.' WHERE mo_name LIKE '%Долгоруковский%';
UPDATE dim_mo SET leader_name = 'Семенихин О.Н.' WHERE mo_name LIKE '%Елецкий%';
UPDATE dim_mo SET leader_name = 'Щедров А.И.' WHERE mo_name LIKE '%Задонский%';
UPDATE dim_mo SET leader_name = 'Иванников В.Ю.' WHERE mo_name LIKE '%Измалковский%';
UPDATE dim_mo SET leader_name = 'Поляков С.О.' WHERE mo_name LIKE '%Краснинский%';
UPDATE dim_mo SET leader_name = 'Телков А.М.' WHERE mo_name LIKE '%Лебедянский%';
UPDATE dim_mo SET leader_name = 'Шабанов К.Ю.' WHERE mo_name LIKE '%Лев-Толстовский%';
UPDATE dim_mo SET leader_name = 'Тодуа Д.В.' WHERE mo_name LIKE '%Липецкий%';
UPDATE dim_mo SET leader_name = 'Семянников Д.Ю.' WHERE mo_name LIKE '%Становлянский%';
UPDATE dim_mo SET leader_name = 'Черников Н.Е.' WHERE mo_name LIKE '%Тербунский%';
UPDATE dim_mo SET leader_name = 'Мазо В.М.' WHERE mo_name LIKE '%Усманский%';
UPDATE dim_mo SET leader_name = 'Плотников А.И.' WHERE mo_name LIKE '%Хлевенский%';
UPDATE dim_mo SET leader_name = 'Сазонов Ю.А.' WHERE mo_name LIKE '%Чаплыгинский%';

COMMIT;
EOSQL

PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -f /tmp/update_leaders.sql 2>&1 | grep -E "^UPDATE|^COMMIT"

rm -f /tmp/update_leaders.sql

echo ""
echo -e "${GREEN}✅ Leader names populated successfully${NC}"
echo ""

# Step 3: Verification
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Verification: Checking migration results...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check column exists
echo -e "${YELLOW}1. Checking leader_name column:${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='dim_mo' AND column_name='leader_name';" 2>&1

echo ""
echo -e "${YELLOW}2. Checking populated records:${NC}"
COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -tA -c "SELECT COUNT(*) FROM dim_mo WHERE leader_name IS NOT NULL;")

echo "Records with leader names: $COUNT"

echo ""
echo -e "${YELLOW}3. Sample data:${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "SELECT mo_id, mo_name, leader_name FROM dim_mo WHERE leader_name IS NOT NULL LIMIT 5;" 2>&1

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Migration completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Verify in browser: https://reyting-alex1976.amvera.io"
echo "2. Check API: curl 'https://reyting-alex1976.amvera.io/api/rating?period=2024-01&page=1'"
echo "3. Go to Rating tab - should show leader names in table"
echo ""
echo -e "${YELLOW}🔍 Troubleshooting:${NC}"
echo "- If leader names are empty, check MO names format in database"
echo "- Use: SELECT DISTINCT mo_name FROM dim_mo ORDER BY mo_name;"
echo ""
