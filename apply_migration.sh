#!/bin/bash

# Скрипт для применения миграции на Amvera PostgreSQL БД
# Использование: ./apply_migration.sh [password]

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры БД
DB_HOST="amvera-alex1976-cnpq-reyting-mo-rw"
DB_PORT="5432"
DB_NAME="reytingdb"
DB_USER="reyting_user"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Применение миграции на Amvera PostgreSQL БД${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Получить пароль
if [ -z "$1" ]; then
    echo -e "${RED}❌ Ошибка: пароль не передан${NC}"
    echo ""
    echo "Использование: $0 <password>"
    echo ""
    echo "Пример:"
    echo "  $0 'my_password'"
    echo ""
    echo "Или установите переменную окружения:"
    echo "  export PGPASSWORD='my_password'"
    echo "  $0"
    exit 1
fi

DB_PASSWORD="$1"

# Проверить подключение
echo -e "${YELLOW}📡 Проверка подключения к БД...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Подключение успешно${NC}"
else
    echo -e "${RED}❌ Не удалось подключиться к БД${NC}"
    echo -e "${RED}Проверьте параметры подключения:${NC}"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔄 Применение миграции...${NC}"
echo ""

# Применить миграцию - добавить колонку
echo -e "${YELLOW}1. Добавление колонки leader_name...${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "ALTER TABLE dim_mo ADD COLUMN IF NOT EXISTS leader_name VARCHAR(255);" 2>&1 | grep -v "^$"

echo ""

# Создать индекс
echo -e "${YELLOW}2. Создание индекса...${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "CREATE INDEX IF NOT EXISTS idx_dim_mo_leader_name ON dim_mo(leader_name);" 2>&1 | grep -v "^$"

echo ""

# Проверить результат
echo -e "${YELLOW}3. Проверка результата...${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='dim_mo' AND column_name='leader_name';" 2>&1

echo ""
echo -e "${GREEN}✅ Миграция успешно применена!${NC}"
echo ""

# Показать статистику
echo -e "${YELLOW}📊 Информация о таблице:${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" \
  -c "\d dim_mo" 2>&1 | head -20

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Миграция завершена успешно!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Дальше вы можете:"
echo "1. Заполнить ФИО глав МО:"
echo "   PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -f backend/migrations/sample_leader_data.sql"
echo ""
echo "2. Заполнить рейтинговые данные:"
echo "   PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -f etl/fill_rating_data_compact.sql"
echo ""
echo "3. Проверить API:"
echo "   curl 'https://reyting-alex1976.amvera.io/api/rating?period=2024-01&page=1'"
