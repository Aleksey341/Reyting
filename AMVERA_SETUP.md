# Amvera Setup - Настройка проекта для работы с Amvera PostgreSQL

## 📍 Параметры подключения к Amvera БД

**Хост подключения:**
```
amvera-alex1976-cnpq-reyting-mo-rw
```

**Полная строка подключения:**
```
postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
```

## 🔧 Быстрые примеры подключения

### 1. psql (командная строка)

```bash
psql "postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
```

### 2. Node.js (pg модуль)

```javascript
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,        // amvera-alex1976-cnpq-reyting-mo-rw
  port: 5432,
  database: process.env.DB_NAME,    // reytingdb
  user: process.env.DB_USER,        // reyting_user
  password: process.env.DB_PASSWORD,
});

// Использование
const result = await pool.query('SELECT * FROM dim_mo');
```

### 3. SQLAlchemy (Python)

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb",
    pool_pre_ping=True  # Проверка соединения перед использованием
)

# Использование с ORM
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()
```

### 4. Prisma (Node.js ORM)

```env
# .env или .env.local
DATABASE_URL="postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
```

```javascript
// prisma.js
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()
```

## 🌐 Внешний доступ (с вашего ПК)

### Вариант 1: pgAdmin через Amvera (рекомендуется)

1. Откройте консоль Amvera
2. Нажмите "Деплой pgAdmin" рядом с БД
3. Подключитесь через браузер

### Вариант 2: Прямое подключение

Если в Amvera включен публичный доступ:
- Используйте публичный Host (выдан отдельно)
- Или настройте SSH туннель

Проверьте вкладку "Доступ" в консоли Amvera для деталей.

## ⚙️ Конфигурация проекта

### Backend (FastAPI)

**backend/config.py:**
```python
database_url: str = os.getenv(
    "DATABASE_URL",
    "postgresql://reyting_user:password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
)
```

**Установка переменной окружения:**

Linux/Mac:
```bash
export DATABASE_URL="postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
```

Windows (CMD):
```cmd
set DATABASE_URL=postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
```

Windows (PowerShell):
```powershell
$env:DATABASE_URL="postgresql://reyting_user:<пароль>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
```

### Frontend (React)

**frontend/.env:**
```env
REACT_APP_API_URL=http://localhost:8000/api
```

**Для production:**
```env
REACT_APP_API_URL=https://your-backend-domain.com/api
```

### Docker Compose (локально)

Если хотите использовать локальный PostgreSQL, оставьте текущую конфигурацию.
Для Amvera - установите переменную `DATABASE_URL` перед запуском.

## 📝 Файлы конфигурации

### .env.example

```env
# Database Configuration
# For local development:
# DATABASE_URL=postgresql://dashboard_user:dashboard_password@localhost:5432/dashboard_db

# For Amvera production:
DATABASE_URL=postgresql://reyting_user:YOUR_PASSWORD_HERE@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb

# Backend Configuration
DEBUG=True
API_TITLE=Dashboard API
API_VERSION=1.0.0

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api
```

### .env (используется только локально, в .gitignore)

```env
DATABASE_URL=postgresql://reyting_user:your_actual_password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
DEBUG=False
```

## 🔒 Безопасность

### Пароль в DATABASE_URL

**❌ НИКОГДА не коммитьте пароль в код!**

1. Используйте переменные окружения
2. Сохраняйте в `.env` (должен быть в `.gitignore`)
3. В Amvera - используйте переменные окружения деплоя

### Рекомендуемое хранение паролей

**Локально:**
```bash
# Создайте .env файл (автоматически в .gitignore)
cat > .env << EOF
DATABASE_URL=postgresql://reyting_user:YOUR_PASSWORD@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
EOF

# Используйте python-dotenv в backend
from dotenv import load_dotenv
load_dotenv()
```

**В Amvera:**
1. Откройте консоль Amvera
2. Перейдите в Settings > Environment Variables
3. Добавьте `DATABASE_URL` с вашим паролем
4. Deploy автоматически подхватит переменную

## 🔍 Частые нюансы Amvera

### 1. RO и RW хосты

Если БД поддерживает реплики:
- `-rw` хост: для записи (основной)
- `-ro` хост: для чтения (реплика)

**Используйте `-rw` для приложения:**
```
amvera-alex1976-cnpq-reyting-mo-rw  ✓ Для записи
amvera-alex1976-cnpq-reyting-mo-ro  ✓ Только для чтения (если нужно)
```

### 2. SSL/TLS

Многие кластеры Amvera работают без обязательного SSL.

Если требуется SSL, добавьте в DATABASE_URL:
```
postgresql://user:pass@host:5432/db?sslmode=require
```

Проверьте вкладку "Доступ" вашей БД в Amvera.

### 3. Пулирование соединений

Используйте `pool_pre_ping=True` в SQLAlchemy:
```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверяет соединение перед запросом
    pool_size=10,
    max_overflow=20
)
```

### 4. Таймауты

Если возникают проблемы с таймаутами:
```python
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30 сек
    }
)
```

## 📊 Инициализация БД

### Загрузить схему из файла

```bash
# Локально через Docker
docker-compose exec postgres psql -U dashboard_user -d dashboard_db < database_schema.sql

# Через Amvera (внешний доступ)
psql "postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb" < database_schema.sql
```

### Загрузить тестовые данные

```bash
# Через Python ETL скрипт
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
python ../etl/load_csv_data.py
```

## ✅ Проверка подключения

### 1. Через psql

```bash
psql "postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb" -c "SELECT 1"
```

### 2. Через Python

```python
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✓ Connection successful!")
```

### 3. Через Node.js

```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: 'postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb'
});

pool.query('SELECT 1', (err, res) => {
  if (err) console.error('✗ Connection failed:', err);
  else console.log('✓ Connection successful!');
});
```

## 🚀 Развёртывание на Amvera

### Метод 1: Docker контейнер

1. Подготовить Dockerfile
2. Загрузить на Amvera
3. Установить переменные окружения
4. Deploy

### Метод 2: GitHub Integration

1. Залить код на GitHub (уже сделано ✓)
2. В Amvera подключить GitHub
3. Выбрать ветку `main`
4. Настроить переменные окружения
5. Auto-deploy при push

## 📞 Поддержка

- **Amvera документация**: https://amvera.ru/docs
- **PostgreSQL docs**: https://www.postgresql.org/docs/
- **SQLAlchemy docs**: https://docs.sqlalchemy.org/
- **Проект GitHub**: https://github.com/Aleksey341/Reyting

---

**Последнее обновление**: 2024-11-04
**Версия**: 1.0.0 + Amvera
