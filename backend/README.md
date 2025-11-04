# Backend - Dashboard API

FastAPI-based backend for the Lipetsk region governance effectiveness dashboard.

## Features

- RESTful API for map, rating, indicators, and methodology
- PostgreSQL database with SQLAlchemy ORM
- File upload handling (CSV, Excel)
- Data validation and quality checks
- Comprehensive logging and error handling

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── database.py          # Database connection and session setup
├── models.py            # SQLAlchemy ORM models
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── routes/
│   ├── map_routes.py       # Map and MO detail endpoints
│   ├── rating_routes.py    # Rating and comparison endpoints
│   ├── indicator_routes.py # Indicator data endpoints
│   ├── methodology_routes.py # Methodology version endpoints
│   └── upload_routes.py    # File upload endpoints
└── tests/               # Unit tests
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/database"
   ```

3. **Run locally:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Map
- `GET /api/map?period=YYYY-MM&version=1` - Map data with MO scores
- `GET /api/map/{mo_id}` - Detailed MO information

### Rating
- `GET /api/rating?period=YYYY-MM&sort=score_total&page=1` - Rating table
- `GET /api/rating/comparison?mo_ids=1,2,3` - Compare multiple MOs

### Indicators
- `GET /api/indicators?block=Public&is_public=true` - List indicators
- `GET /api/indicators/{mo_id}?period_id=1` - MO indicators

### Methodology
- `GET /api/methodology/versions` - Available methodology versions
- `GET /api/methodology/{version_id}/scales` - Color zones/scales

### Upload
- `POST /api/upload/{source_id}` - Upload data file
- `GET /api/upload/uploads/{upload_id}` - Check upload status

## Database Schema

See `../database_schema.sql` for complete schema definition including:
- Dimension tables (MO, periods, indicators, penalties, methodology)
- Fact tables (indicators, penalties, events, summaries)
- Audit and quality control tables

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Style
```bash
black .
flake8 .
```

## Docker

Build and run with Docker Compose:
```bash
cd ..
docker-compose up --build
```

## Authentication & Authorization

Currently no authentication. Planned features:
- OIDC/LDAP integration
- Role-based access control (RBAC)
- Mask sensitive data based on user roles
