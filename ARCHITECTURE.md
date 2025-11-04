# Architecture - Архитектура системы Dashboard

## Архитектурный обзор

```
┌─────────────────────────────────────────────────────┐
│                    Web Browser                      │
│              (Chrome, Firefox, Safari)              │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────┐
│          Frontend (React 18 + Tailwind)             │
│                                                     │
│  ├─ MapPage        - Choropleth visualization      │
│  ├─ RatingPage     - Table with sorting/pagination │
│  ├─ AnalyticsPage  - Indicator dashboard           │
│  ├─ Header         - Navigation & period selector  │
│  └─ Sidebar        - Main menu                     │
└────────────────────┬────────────────────────────────┘
                     │ RESTful JSON API
┌────────────────────▼────────────────────────────────┐
│        Backend API (FastAPI + SQLAlchemy)           │
│                                                     │
│  Routes:                                            │
│  ├─ /api/map/*              - Map data              │
│  ├─ /api/rating/*           - Rating tables         │
│  ├─ /api/indicators/*       - Indicator data        │
│  ├─ /api/methodology/*      - Methodology versions  │
│  └─ /api/upload/*           - File uploads          │
│                                                     │
│  Core Services:                                     │
│  ├─ Database ORM             - SQLAlchemy           │
│  ├─ Data Validation          - Pydantic             │
│  ├─ Error Handling           - Exception handlers   │
│  └─ Logging                  - Structured logs      │
└────────────────────┬────────────────────────────────┘
                     │ SQL
┌────────────────────▼────────────────────────────────┐
│     PostgreSQL 15 + PostGIS (Spatial Database)      │
│                                                     │
│  Dimensions (Reference Data):                       │
│  ├─ dim_mo             - Municipal organizations   │
│  ├─ dim_period         - Time periods              │
│  ├─ dim_indicator      - Metrics definitions       │
│  ├─ dim_penalty        - Penalty definitions       │
│  ├─ dim_methodology    - Methodology versions      │
│  └─ map_scale          - Color/zone mappings       │
│                                                     │
│  Facts (Operational Data):                          │
│  ├─ fact_indicator     - Metric values             │
│  ├─ fact_penalty       - Applied penalties         │
│  ├─ fact_summary       - Aggregated scores         │
│  └─ fact_events        - Events/incidents          │
│                                                     │
│  Service Tables:                                    │
│  ├─ audit_log          - Change tracking           │
│  ├─ upload_log         - File upload history       │
│  ├─ src_registry       - Data sources              │
│  └─ data_quality_flags - Quality issues            │
└─────────────────────────────────────────────────────┘
```

## Компонентная архитектура

### 1. Frontend (React 18)

```
App.jsx (Router)
├── Header
│   ├── Period selector
│   ├── Menu toggle
│   └── Version info
├── Sidebar
│   ├── Map link
│   ├── Rating link
│   └── Analytics link
└── Routes
    ├── MapPage
    │   ├── Map visualization
    │   ├── Zone statistics
    │   └── MO detail panel
    ├── RatingPage
    │   ├── Sortable table
    │   ├── Pagination
    │   └── Filter options
    └── AnalyticsPage
        ├── Indicator cards
        ├── Block filters
        └── Metadata display
```

### 2. Backend (FastAPI)

```
main.py (FastAPI App)
├── routes/
│   ├── map_routes.py
│   │   ├── GET /map          - All MO data
│   │   └── GET /map/{mo_id}  - Single MO details
│   ├── rating_routes.py
│   │   ├── GET /rating       - Rating table
│   │   └── GET /comparison   - MO comparison
│   ├── indicator_routes.py
│   │   ├── GET /indicators   - All indicators
│   │   └── GET /indicators/{mo_id} - MO indicators
│   ├── methodology_routes.py
│   │   ├── GET /versions     - Methodology versions
│   │   └── GET /{id}/scales  - Zone definitions
│   └── upload_routes.py
│       ├── POST /upload/{source_id} - Upload file
│       └── GET /uploads/{upload_id}  - Upload status
├── models.py - SQLAlchemy ORM models
├── database.py - Connection management
└── config.py - Configuration
```

### 3. Database (PostgreSQL)

```
dashboard_db
├── Schema: public
│   ├── Tables (Dimensions)
│   │   ├── dim_mo (20 records)
│   │   ├── dim_period (months/halfyears/years)
│   │   ├── dim_indicator (9+ metrics)
│   │   ├── dim_penalty (3+ penalty types)
│   │   ├── dim_methodology (versions)
│   │   ├── map_scale (zone mappings)
│   │   └── src_registry (data sources)
│   │
│   ├── Tables (Facts)
│   │   ├── fact_indicator
│   │   ├── fact_penalty
│   │   ├── fact_summary
│   │   └── fact_events
│   │
│   ├── Tables (Service)
│   │   ├── audit_log
│   │   ├── upload_log
│   │   └── data_quality_flags
│   │
│   └── Indexes (Performance)
│       ├── idx_fact_indicator_mo_period
│       ├── idx_fact_summary_mo_period
│       └── idx_audit_log_ts
```

## Data Flow

### 1. Входящие данные (ETL)

```
CSV/Excel Files
    ↓
ETL Validation
├─ Type checking
├─ Range validation
├─ Required fields
└─ Duplicates
    ↓
Data Transformation
├─ Normalize values
├─ Calculate scores
└─ Apply methodology
    ↓
Database Insert
├─ Batch operations
├─ Transaction handling
└─ Audit logging
    ↓
Calculated Fields
├─ Score aggregation
├─ Zone assignment
└─ Quality flags
```

### 2. Запросы данных (Read Path)

```
Frontend Request
├─ HTTP GET /api/rating
├─ Query params: period, sort, page
    ↓
Backend Processing
├─ Database query
├─ Data validation
├─ Format response
    ↓
Response to Frontend
├─ JSON payload
├─ Status codes
└─ Error messages
    ↓
Frontend Rendering
├─ Parse JSON
├─ Update state
└─ Render UI
```

## Поток данных по периодам

```
Месячные срезы (Monthly)
├─ Каждый месяц
├─ Данные от ведомств
└─ Промежуточные метрики

Полугодовые срезы (Half-yearly)
├─ Июль и Январь (по ТЗ)
├─ Финальная публикация
├─ Все метрики агрегированы
└─ Официальный рейтинг

Версионирование методики
├─ v1.0 - текущая
├─ Пересчёт по версии
└─ Исторические данные сохранены
```

## Security Architecture

```
┌─────────────────────────────────────────┐
│   User Authentication Layer (Future)    │
│   ├─ OIDC/LDAP                          │
│   └─ JWT tokens                         │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────▼───────────────────┐
│   Authorization Layer (RBAC)            │
│   ├─ Governor             (all data)    │
│   ├─ Ministry             (own metrics) │
│   ├─ MO Head             (limited view) │
│   └─ Public              (published)    │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────▼───────────────────┐
│   Data Masking Layer                    │
│   ├─ Hide closed metrics (non-approved) │
│   ├─ Anonymize sensitive data           │
│   └─ Audit all access                   │
└─────────────────────────────────────────┘
```

## Performance Optimization

### Frontend
```
Performance Target: TTFB ≤ 1.5s

├─ Code Splitting
│   └─ Lazy load pages
├─ Image Optimization
│   └─ Responsive images
├─ Bundle Size
│   └─ Minimize dependencies
└─ Caching
    └─ Browser cache for static assets
```

### Backend
```
Performance Target: API Response ≤ 1s

├─ Database Indexing
│   ├─ Foreign keys indexed
│   ├─ Frequent filters indexed
│   └─ Join columns indexed
├─ Query Optimization
│   ├─ Use projections
│   ├─ Batch operations
│   └─ Connection pooling
├─ Caching Layer (Future)
│   ├─ Redis for hot data
│   └─ Query result cache
└─ Load Balancing (Future)
    └─ Multiple backend instances
```

## Scalability

### Horizontal Scaling (Future)
```
┌─────────────────────┐
│   Load Balancer     │
│  (Nginx/HAProxy)    │
└──────────┬──────────┘
           │
      ┌────┴───┬────────┐
      │         │        │
   ┌──▼──┐  ┌──▼──┐  ┌──▼──┐
   │API-1│  │API-2│  │API-N│
   └──┬──┘  └──┬──┘  └──┬──┘
      │         │        │
      └────┬────┴────┬───┘
           │         │
      ┌────▼────┐  ┌─▼────┐
      │ Primary │  │ Read  │
      │Database │  │ Replicas│
      └─────────┘  └───────┘
```

### Database Replication (Future)
```
Main PostgreSQL
├─ Streaming replication
├─ WAL archiving
└─ Point-in-time recovery

Read-Only Replicas
├─ Read scaling
├─ Backup support
└─ Failover ready
```

## Deployment Architecture

### Development
```
Single Docker Compose with all services
├─ Frontend (port 3000)
├─ Backend (port 8000)
└─ PostgreSQL (port 5432)
```

### Staging
```
Docker Swarm / Kubernetes (Future)
├─ Frontend service (3 replicas)
├─ Backend service (2 replicas)
├─ PostgreSQL (persistent volume)
└─ Reverse proxy (Nginx)
```

### Production
```
Kubernetes Cluster
├─ Frontend deployment
│   ├─ CDN for static
│   └─ Auto-scaling
├─ Backend deployment
│   ├─ Stateless services
│   ├─ Auto-scaling
│   └─ Health checks
├─ PostgreSQL
│   ├─ CloudSQL or managed
│   └─ Backups & HA
└─ Monitoring
    ├─ Prometheus
    ├─ Grafana
    └─ ELK Stack
```

## Technology Decisions

| Component | Choice | Reason |
|-----------|--------|--------|
| Frontend Framework | React 18 | Popular, component-based, large community |
| Styling | Tailwind CSS | Utility-first, fast development |
| Backend Framework | FastAPI | Modern, async, auto-docs, performance |
| Database | PostgreSQL | ACID, PostGIS, spatial support, open-source |
| ORM | SQLAlchemy | Flexible, well-tested, comprehensive |
| Containerization | Docker | Portable, reproducible, industry-standard |
| Orchestration | Docker Compose | Simple for dev, Kubernetes for production |
| API Documentation | Swagger/ReDoc | Auto-generated from FastAPI |

## Extension Points

### Adding new data source
1. Create `etl/load_<source>.py`
2. Register in `src_registry`
3. Map to `dim_indicator`
4. Run ETL pipeline

### Adding new metric
1. Create row in `dim_indicator`
2. Add `fact_indicator` records
3. Include in aggregation logic
4. Update frontend to display

### Adding new user role
1. Define permissions
2. Implement authorization filter
3. Mask sensitive fields
4. Log all access

### Adding new UI page
1. Create component in `frontend/src/pages/`
2. Add route in `App.jsx`
3. Add navigation in Sidebar
4. Create corresponding API endpoints

## Monitoring & Observability

### Logging
```
├─ Backend
│   ├─ Application logs (INFO/ERROR)
│   ├─ Database query logs
│   └─ API request/response logs
├─ Frontend
│   ├─ Console errors
│   ├─ Performance metrics
│   └─ User interactions
└─ Database
    ├─ Slow query log
    ├─ Connection errors
    └─ Backup status
```

### Metrics (Future)
```
├─ API Performance
│   ├─ Response time p99
│   ├─ Error rate
│   └─ Request volume
├─ Database
│   ├─ Query latency
│   ├─ Connection pool usage
│   └─ Replication lag
└─ Frontend
    ├─ Page load time
    ├─ Core Web Vitals
    └─ User engagement
```

## Disaster Recovery

```
RTO: 1 hour (Recovery Time Objective)
RPO: 15 minutes (Recovery Point Objective)

├─ Daily automated backups
├─ Point-in-time recovery capability
├─ Database replication
├─ Backup testing (weekly)
└─ Documented runbooks
```

---

**Last Updated**: 2024-11-04
**Version**: 1.0.0
**Author**: Development Team
