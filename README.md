# Dashboard - Интерактивный дашборд оценки эффективности глав МО Липецкой области

Полнофункциональное веб-приложение для управления и анализа эффективности муниципальных образований Липецкой области на основе утверждённой методики оценки.

## Обзор проекта

Проект реализует следующие функции:

- **Интерактивная карта** с хлороплетой по муниципальным образованиям
- **Рейтинги** (публичные и закрытые) с поддержкой сравнения
- **Аналитика** по индикаторам и показателям
- **Управление методикой** с версионированием
- **Загрузка данных** из различных источников (CSV, Excel, API)
- **Ролевой доступ** с маскированием чувствительных данных

## Архитектура

```
┌─────────────────────────────────────────────┐
│         Frontend (React + MapLibre)         │
│  - Map, Rating, Analytics, Components       │
│  - Tailwind CSS, responsive UI              │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST
┌──────────────────┴──────────────────────────┐
│      Backend API (FastAPI + SQLAlchemy)     │
│  - Map, Rating, Indicator, Methodology APIs │
│  - File upload, data validation             │
└──────────────────┬──────────────────────────┘
                   │ SQL
┌──────────────────┴──────────────────────────┐
│   Database (PostgreSQL 15 + PostGIS)        │
│  - Dimension & fact tables, audit logs      │
│  - GeoJSON support for map rendering        │
└─────────────────────────────────────────────┘
```

## Технологический стек

### Backend
- **Framework**: FastAPI 0.104
- **Database**: PostgreSQL 15 + PostGIS
- **ORM**: SQLAlchemy 2.0
- **Data**: Pandas, GeoPandas
- **Server**: Uvicorn

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS 3
- **Maps**: MapLibre GL
- **Charts**: Recharts/ECharts
- **HTTP**: Axios

### DevOps
- **Containerization**: Docker & Docker Compose
- **CI/CD**: Ready for integration
- **Version Control**: Git

## Требования

- Docker & Docker Compose 3.8+
- Python 3.11+ (для локальной разработки)
- Node.js 18+ (для локальной разработки)
- PostgreSQL 15 (автоматически в Docker)

## Быстрый старт

### Подключение к Amvera PostgreSQL

**Параметры подключения:**
```
Host: amvera-alex1976-cnpq-reyting-mo-rw
Port: 5432
Database: reytingdb
User: reyting_user
Password: [получить в Amvera консоли]
```

**Примеры подключения:**

Python (SQLAlchemy):
```python
engine = create_engine(
    "postgresql+psycopg2://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb",
    pool_pre_ping=True
)
```

Node.js (pg):
```javascript
const { Pool } = require('pg');
const pool = new Pool({
  host: 'amvera-alex1976-cnpq-reyting-mo-rw',
  port: 5432,
  database: 'reytingdb',
  user: 'reyting_user',
  password: process.env.DB_PASSWORD,
});
```

psql (консоль):
```bash
psql "postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"
```

### С Docker Compose (локально)

```bash
# Клонировать репозиторий
git clone https://github.com/Aleksey341/Reyting.git
cd Reyting

# Запустить все сервисы (используется локальный PostgreSQL)
docker-compose up --build

# Приложение будет доступно:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Database: localhost:5432 (Docker)
```

### Локальная разработка с Amvera БД

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Установить переменную окружения с паролем Amvera
export DATABASE_URL="postgresql://reyting_user:<password>@amvera-alex1976-cnpq-reyting-mo-rw:5432/reytingdb"

# Запустить сервер
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
export REACT_APP_API_URL=http://localhost:8000/api
npm start
```

## Структура проекта

```
Проект/
├── backend/                    # FastAPI приложение
│   ├── main.py                # Точка входа
│   ├── config.py              # Конфигурация
│   ├── database.py            # Подключение БД
│   ├── models.py              # SQLAlchemy модели
│   ├── routes/                # API endpoints
│   │   ├── map_routes.py
│   │   ├── rating_routes.py
│   │   ├── indicator_routes.py
│   │   ├── methodology_routes.py
│   │   └── upload_routes.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                   # React приложение
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.jsx
│   │   ├── components/        # React компоненты
│   │   ├── pages/             # Страницы приложения
│   │   └── services/          # API клиент
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   ├── tailwind.config.js
│   └── README.md
│
├── database_schema.sql         # SQL схема БД
├── docker-compose.yml          # Docker Compose конфигурация
├── .gitignore
└── README.md                   # Этот файл
```

## API Endpoints

### Карта
- `GET /api/map?period=YYYY-MM` - Данные карты с баллами МО
- `GET /api/map/{mo_id}` - Детали конкретного МО

### Рейтинг
- `GET /api/rating?period=YYYY-MM&sort=score_total` - Таблица рейтинга
- `GET /api/rating/comparison?mo_ids=1,2,3` - Сравнение МО

### Показатели
- `GET /api/indicators?block=Public` - Список показателей
- `GET /api/indicators/{mo_id}` - Показатели МО

### Методика
- `GET /api/methodology/versions` - Версии методики
- `GET /api/methodology/{version_id}/scales` - Шкалы оценки

### Загрузка
- `POST /api/upload/{source_id}` - Загрузить файл
- `GET /api/upload/uploads/{upload_id}` - Статус загрузки

Полная документация доступна в Swagger: `http://localhost:8000/docs`

## Модель данных

### Справочники (Dimensions)
- `dim_mo` - Муниципальные образования
- `dim_period` - Периоды (месяцы, полугодия, года)
- `dim_indicator` - Показатели/критерии
- `dim_penalty` - Штрафные баллы
- `dim_methodology` - Версии методики
- `map_scale` - Шкалы оценки (зоны)

### Факты (Facts)
- `fact_indicator` - Значения показателей по МО/периодам
- `fact_penalty` - Штрафы и события
- `fact_summary` - Итоговые баллы
- `fact_events` - События (встречи, конфликты и т.д.)

### Служебные таблицы
- `audit_log` - Журнал всех изменений
- `upload_log` - История загрузок
- `data_quality_flags` - Флаги качества данных

## Методика оценки

### Интегральная шкала (светофор)
- **Зелёная зона**: 53-66 баллов - Высокая эффективность
- **Жёлтая зона**: 29-52 балла - Средняя эффективность
- **Красная зона**: 0-28 баллов - Низкая эффективность

### Структура баллов
- **Публичный рейтинг**: макс. 31 балл (9 показателей)
- **Закрытый рейтинг**: макс. 35 баллов (8 показателей)
- **Штрафные баллы**: отрицательные баллы за события
- **Итого**: score_public + score_closed + score_penalties

## Использование

### Просмотр карты
1. Откройте `http://localhost:3000`
2. Выберите период в панели фильтров
3. Нажмите на МО для просмотра детальной информации
4. Используйте легенду для понимания цветовой схемы

### Просмотр рейтинга
1. Перейдите на вкладку "Рейтинг"
2. Отсортируйте по нужному критерию
3. Используйте пагинацию для навигации

### Загрузка данных
1. Подготовьте файл в формате CSV или Excel
2. В Backend: `POST /api/upload/{source_id}`
3. Система автоматически обработает и валидирует данные

## Тестирование

### Backend
```bash
cd backend
pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm test
```

## Развёртывание

### На production сервер

1. **Подготовка**
   ```bash
   git clone <repo-url>
   cd Проект
   cp .env.example .env
   # Отредактировать .env с production параметрами
   ```

2. **Запуск**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Проверка**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

4. **Бэкапы**
   ```bash
   docker-compose exec postgres pg_dump -U dashboard_user dashboard_db > backup.sql
   ```

## Логирование и мониторинг

- Backend логи: `docker-compose logs -f backend`
- Frontend логи: `docker-compose logs -f frontend`
- Database логи: `docker-compose logs -f postgres`

## Безопасность

- [ ] Добавить HTTPS/TLS
- [ ] Реализовать OIDC/LDAP аутентификацию
- [ ] Добавить цифровые подписи файлов
- [ ] Шифрование чувствительных данных
- [ ] Rate limiting для API

## Проблемы и решение

### Port уже в использовании
```bash
# Изменить порты в docker-compose.yml или:
docker-compose -p dashboard down
```

### Database connection error
```bash
# Проверить PostgreSQL контейнер
docker-compose logs postgres
# Переинициализировать БД
docker-compose down -v
docker-compose up
```

## Roadmap

- [ ] Версия 1.1: Экспорт в PDF/Excel
- [ ] Версия 1.2: Интеграция с API ведомств
- [ ] Версия 1.3: Мобильное приложение
- [ ] Версия 2.0: Расширенная аналитика и предсказания

## Контакты и поддержка

- **Email**: support@example.com
- **Issues**: GitHub Issues
- **Documentation**: `/docs`

## Лицензия

[Укажите лицензию проекта]

## Благодарности

Разработано для Администрации Липецкой области.

---

**Последнее обновление**: 2024-11-04
**Версия**: 1.0.0
**Статус**: Beta
