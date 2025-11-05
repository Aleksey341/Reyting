# ⚡ Performance Optimization Guide

Рекомендации по оптимизации производительности для production.

---

## 📊 Текущее состояние

На этапе MVP:
- ✅ Seed данные загружены (~13k записей)
- ✅ API endpoints готовы
- ✅ Frontend может работать
- ⏳ Production трафик еще не начался

**Оптимизация нужна только если:**
- Responses > 500ms
- Database queries > 1 second
- High CPU/Memory usage in Amvera

---

## 🗄️ Database Optimization

### Phase 1: Add Indexes (CRITICAL)

Добавьте индексы на часто фильтруемые поля:

```sql
-- Foreign keys (most important)
CREATE INDEX idx_fact_indicator_mo_id
  ON fact_indicator(mo_id);

CREATE INDEX idx_fact_indicator_period_id
  ON fact_indicator(period_id);

CREATE INDEX idx_fact_indicator_ind_id
  ON fact_indicator(ind_id);

CREATE INDEX idx_fact_summary_mo_id
  ON fact_summary(mo_id);

CREATE INDEX idx_fact_summary_period_id
  ON fact_summary(period_id);

-- Dimension table lookups
CREATE INDEX idx_dim_mo_name
  ON dim_mo(mo_name);

CREATE INDEX idx_dim_indicator_code
  ON dim_indicator(code);

-- Composite indexes for common queries
CREATE INDEX idx_fact_indicator_composite
  ON fact_indicator(mo_id, period_id, ind_id);

CREATE INDEX idx_fact_summary_composite
  ON fact_summary(mo_id, period_id);
```

**When to add:**
- After first load test shows slow queries
- When /api/rating response > 500ms
- If database logs show sequential scans

**Check index usage:**
```sql
-- Find missing indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- Never used indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check slow queries (requires log_min_duration_statement = 0)
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Phase 2: Materialized Views (IF NEEDED)

Если сложные агрегирующие запросы медленные:

```sql
-- Example: Pre-calculated MO rankings
CREATE MATERIALIZED VIEW mv_mo_rankings AS
SELECT
  m.mo_id,
  m.mo_name,
  fs.score_total,
  fs.zone,
  RANK() OVER (ORDER BY fs.score_total DESC) as rank
FROM dim_mo m
LEFT JOIN fact_summary fs ON m.mo_id = fs.mo_id
WHERE fs.period_id = (
  SELECT period_id FROM dim_period
  ORDER BY date_from DESC LIMIT 1
);

-- Refresh периодически (через cron)
REFRESH MATERIALIZED VIEW mv_mo_rankings;
```

### Phase 3: Query Optimization

Если запросы медленные:

```python
# В backend/routes - оптимизированный запрос
from sqlalchemy import select, func

@router.get("/rating")
def get_rating(session: Session):
    # ✅ GOOD: Single query with joins
    query = (
        select(
            DimMO.mo_id,
            DimMO.mo_name,
            FactSummary.score_total
        )
        .join(FactSummary)
        .order_by(FactSummary.score_total.desc())
        .limit(100)
    )

    # ❌ BAD: N+1 queries (one per MO)
    # mos = session.query(DimMO).all()
    # for mo in mos:
    #     summary = session.query(FactSummary).filter(...)
```

---

## 🚀 Backend Optimization

### Uvicorn Workers

Добавьте workers для параллельной обработки:

**В Dockerfile:**
```dockerfile
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "80", \
     "--workers", "4",  # Number of worker processes
     "--proxy-headers"]
```

**When to use:**
- If CPU is underutilized (< 80%)
- When requests queue up
- For I/O-bound operations

**Recommended workers:**
```
workers = (2 * CPU_count) + 1
```

For typical Amvera setup: 2-4 workers

### Connection Pooling

В `backend/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool, QueuePool

# Current (good)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10  # Extra connections if needed
)

# For high concurrency
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Check connection is alive
)
```

### Response Caching

Для часто запрашиваемых данных:

```python
from fastapi import HTTPException
from functools import lru_cache

@lru_cache(maxsize=100)
def get_indicators_cached():
    """Кэшируется на 1 час"""
    # ... fetch indicators
    return indicators

# Или с временем жизни
from cachetools import TTLCache
cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour
```

---

## 🎨 Frontend Optimization

### Build Optimization (Already done with Vite)

✅ Vite already optimizes:
- Code splitting
- Tree shaking
- Asset minification
- Long-term caching hashes

### Runtime Optimization

```javascript
// Good: Load data on demand
const [data, setData] = useState(null);
useEffect(() => {
  api.rating.list().then(setData);
}, []);

// Better: Pagination
const [page, setPage] = useState(1);
useEffect(() => {
  api.rating.list({ page, page_size: 50 }).then(setData);
}, [page]);

// Best: React Query/SWR for caching
import useSWR from 'swr';
const { data } = useSWR(`/api/rating?page=${page}`, fetcher);
```

---

## 📈 Monitoring Performance

### Enable Query Logging

В PostgreSQL:

```sql
-- Temporary: for debugging
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();

-- Permanent check
SHOW log_min_duration_statement;
```

### Check Slow Queries

```bash
# SSH в контейнер или прямое подключение
psql -U reyting_user -d reytingdb

SELECT
  query,
  calls,
  ROUND(mean_time::numeric, 2) as avg_ms,
  ROUND(max_time::numeric, 2) as max_ms
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY mean_time DESC
LIMIT 10;
```

### Frontend Performance

DevTools → Performance tab:
- Check bundle size
- Identify slow renders
- Monitor network waterfall

```bash
# Check bundle size
npm run build
# Look for dist/assets/ folder size
ls -lh dist/assets/
```

---

## 🎯 Optimization Checklist

### Before Production (MVP)
- [x] CORS configured narrowly
- [x] Health check working
- [x] Seed data loaded
- [ ] Database indexes added (optional for MVP)

### When Getting Slow (Phase 1)
- [ ] Add database indexes
- [ ] Check slow query logs
- [ ] Optimize N+1 queries
- [ ] Enable response caching

### When Scaling (Phase 2)
- [ ] Add API response pagination
- [ ] Implement materialized views
- [ ] Increase uvicorn workers
- [ ] Use Redis caching for hot data
- [ ] Add CDN for static frontend

### When Heavy Load (Phase 3)
- [ ] Database read replicas
- [ ] Query result caching
- [ ] API rate limiting
- [ ] Load balancer with multiple backend instances

---

## 🔍 Quick Performance Check

```bash
# Test response time
time curl https://reyting-alex1976.amvera.io/api/rating | jq '.' > /dev/null

# Check database size
psql -U reyting_user -d reytingdb -c "
  SELECT
    pg_size_pretty(pg_total_relation_size('public.fact_indicator')) as fact_indicator_size,
    COUNT(*) as record_count
  FROM fact_indicator;
"

# Estimate index benefit
psql -U reyting_user -d reytingdb -c "
  SELECT
    schemaname,
    tablename,
    ROUND(pg_total_relation_size(schemaname||'.'||tablename)/1024/1024) as table_mb
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 📚 Resources

- [PostgreSQL Performance Wiki](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [SQLAlchemy Optimization](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/#cpu-intensive-operations)
- [Vite Performance Guide](https://vitejs.dev/guide/troubleshooting.html#vite-cjs-compat)

---

**Версия**: 1.0
**Дата**: 05.11.2025
**Статус**: REFERENCE ✅

Не оптимизируйте раньше, чем появится проблема (YAGNI принцип). Сначала мониторьте!
