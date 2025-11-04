# Развёртывание на Amvera - Пошаговая инструкция

## ❌ Ошибка, которую вы получили

```
Error: error resolving dockerfile path: please provide a valid path to a Dockerfile
within the build context with --dockerfile
```

**Причина**: Amvera не знает, где находятся Dockerfile для backend и frontend.

---

## ✅ Решение

### Вариант 1: Через консоль Amvera (Рекомендуется)

#### Шаг 1: Создать Backend контейнер

1. Откройте консоль Amvera: https://console.amvera.ru
2. Нажмите "Создать новое приложение" или "New Container"
3. Заполните параметры:

   ```
   Name: reyting-backend
   Source: GitHub
   Repository: https://github.com/Aleksey341/Reyting
   Branch: main

   Dockerfile path: backend/Dockerfile  ← ВАЖНО!
   Build context: .

   Port: 8000

   Команда запуска:
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Добавить Environment Variables:**
   ```
   DATABASE_URL: postgresql://reyting_user:<PASSWORD>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb
   DEBUG: False
   PYTHONUNBUFFERED: 1
   ```

5. **Добавить переменные секреты:**
   ```
   DB_PASSWORD: <YOUR_PASSWORD>
   ```

6. Нажмите "Deploy"

#### Шаг 2: Создать Frontend контейнер

1. Создать новое приложение
2. Заполните параметры:

   ```
   Name: reyting-frontend
   Source: GitHub
   Repository: https://github.com/Aleksey341/Reyting
   Branch: main

   Dockerfile path: frontend/Dockerfile  ← ВАЖНО!
   Build context: .

   Port: 3000
   ```

3. **Добавить Environment Variables:**
   ```
   REACT_APP_API_URL: https://reyting-api.amvera.ru/api
   ```

4. Нажмите "Deploy"

#### Шаг 3: Настроить маршрутизацию

1. В консоли Amvera перейдите в "Routing" или "Балансировщик нагрузки"
2. Добавьте правила:

   ```
   /api/* → reyting-backend:8000
   /* → reyting-frontend:3000
   ```

---

### Вариант 2: Через CI/CD (GitHub Actions)

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Amvera

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Deploy backend
      - name: Deploy Backend to Amvera
        run: |
          curl -X POST https://api.amvera.ru/deploy \
            -H "Authorization: Bearer ${{ secrets.AMVERA_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{
              "app_id": "reyting-backend",
              "dockerfile": "backend/Dockerfile",
              "context": "."
            }'

      # Deploy frontend
      - name: Deploy Frontend to Amvera
        run: |
          curl -X POST https://api.amvera.ru/deploy \
            -H "Authorization: Bearer ${{ secrets.AMVERA_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{
              "app_id": "reyting-frontend",
              "dockerfile": "frontend/Dockerfile",
              "context": "."
            }'
```

---

### Вариант 3: Через Docker CLI (Локально)

Если вы хотите использовать Docker напрямую:

```bash
# 1. Авторизоваться в Amvera Registry
docker login registry.amvera.ru

# 2. Собрать и загрузить backend
docker build -f backend/Dockerfile -t registry.amvera.ru/your-account/reyting-backend:latest .
docker push registry.amvera.ru/your-account/reyting-backend:latest

# 3. Собрать и загрузить frontend
docker build -f frontend/Dockerfile -t registry.amvera.ru/your-account/reyting-frontend:latest .
docker push registry.amvera.ru/your-account/reyting-frontend:latest

# 4. В консоли Amvera выбрать эти образы для деплоя
```

---

## 📋 Чек-лист деплоя

- [ ] GitHub репо создан и содержит Dockerfile (в папках backend/ и frontend/)
- [ ] DATABASE_URL корректно указана в Environment Variables
- [ ] DB_PASSWORD установлен в секретах Amvera
- [ ] Backend Dockerfile указывает на `backend/Dockerfile`
- [ ] Frontend Dockerfile указывает на `frontend/Dockerfile`
- [ ] Порты правильные: backend=8000, frontend=3000
- [ ] Маршрутизация настроена (/api/* → backend, /* → frontend)
- [ ] Доменное имя настроено (опционально)
- [ ] CORS включен для production доменов

---

## 🔍 Проверка после деплоя

### 1. Проверить статус контейнеров

В консоли Amvera должны быть "Running":
- reyting-backend
- reyting-frontend

### 2. Проверить логи

```bash
# Backend логи
amvera logs reyting-backend

# Frontend логи
amvera logs reyting-frontend
```

### 3. Проверить доступность

```bash
# API
curl https://reyting-api.amvera.ru/health

# Frontend
curl https://reyting.amvera.ru/

# API Docs
open https://reyting-api.amvera.ru/docs
```

### 4. Проверить подключение к БД

```bash
# Через bash контейнера backend
amvera exec reyting-backend bash

# Внутри контейнера
python -c "
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM dim_mo'))
    print('✓ DB connected! MO count:', result.scalar())
"
```

---

## ❌ Частые ошибки и решения

### Ошибка 1: "Dockerfile not found"

**Решение**: Убедитесь, что путь правильный:
```
✓ backend/Dockerfile
✓ frontend/Dockerfile

✗ /backend/Dockerfile
✗ Dockerfile (без папки)
```

### Ошибка 2: "Connection refused to PostgreSQL"

**Решение**: Проверьте DATABASE_URL:
```bash
# Должно быть
postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb

# НЕ
postgresql://reyting_user:<password>@localhost:5432/reytingdb
```

### Ошибка 3: "Port already in use"

**Решение**: Измените порт в конфигурации Amvera или убедитесь, что контейнер не запущен дважды.

### Ошибка 4: "Frontend не может подключиться к Backend"

**Решение**: Проверьте REACT_APP_API_URL:
```bash
# Должно быть
REACT_APP_API_URL=https://your-api-domain.amvera.ru/api

# НЕ
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_API_URL=http://backend:8000/api
```

### Ошибка 5: "Database schema not initialized"

**Решение**: Загрузите схему:
```bash
psql "postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb" < database_schema.sql
```

---

## 🔒 Безопасность

### Переменные окружения в Amvera

**НИКОГДА не сохраняйте секреты в коде!**

1. Откройте настройки контейнера в консоли Amvera
2. Перейдите в "Environment" или "Переменные окружения"
3. Добавьте переменные:

   **Обычные переменные:**
   ```
   DEBUG=False
   REACT_APP_API_URL=https://api.example.com
   ```

   **Секреты (используйте Special или Secrets):**
   ```
   DATABASE_URL=postgresql://reyting_user:PASSWORD@host/db
   DB_PASSWORD=YOUR_PASSWORD
   ```

### Использование .env файла (локально)

```bash
# Создайте .env
DATABASE_URL=postgresql://reyting_user:password@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb

# Используйте python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

---

## 🚀 Полный процесс деплоя

```
1. Git Push (уже сделано)
   ↓
2. GitHub Actions trigger (опционально)
   ↓
3. Amvera получает код из GitHub
   ↓
4. Kaniko собирает Dockerfile
   ↓
5. Образ загружается в Amvera Registry
   ↓
6. Контейнер запускается
   ↓
7. Healthchecks проверяют статус
   ↓
8. Трафик маршрутизируется на контейнер
   ↓
9. Приложение доступно! ✓
```

---

## 📞 Поддержка

- **Документация Amvera**: https://amvera.ru/docs
- **Support Amvera**: support@amvera.ru
- **GitHub Issues**: https://github.com/Aleksey341/Reyting/issues

---

**Последнее обновление**: 2024-11-04
**Версия**: 1.0.0
