# 🏥 Health Check & Monitoring Guide

Руководство по настройке здоровья приложения, мониторинга и резервного копирования на Amvera.

---

## 🔍 Health Check Endpoint

### Что это?

Health check — это HTTP endpoint, который возвращает статус приложения. Используется:
- Amvera для определения живо ли приложение
- Балансировщиками нагрузки (load balancers)
- Мониторингом для алертов

### Backend Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok",
  "service": "reyting-api"
}
```

**Status Code**: `200 OK`

### Проверка в Amvera

1. **Applications** → **reyting** → **Healthcheck**
2. Должно быть:
   - Endpoint: `/health`
   - Interval: 30 секунд (default)
   - Timeout: 3-10 секунд
   - Retries: 3 попытки

Если статус красный (❌) или желтый (⚠️):
1. Проверьте логи: **Applications** → **reyting** → **Logs**
2. Ищите ошибки при старте (database, imports, и т.д.)
3. Перестартуйте: **Applications** → **reyting** → **Redeploy**

### Локальная проверка

```bash
# Прямая проверка
curl https://reyting-alex1976.amvera.io/health
# {"status":"ok","service":"reyting-api"}

# С заголовками
curl -I https://reyting-alex1976.amvera.io/health
# HTTP/2 200
```

---

## 📊 Health Check Statuses in Amvera

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ Green | Healthy | Normal operation |
| ⚠️ Yellow | Degraded | Monitor, may fail soon |
| ❌ Red | Failed | Service down, Amvera may restart |

Если красный несколько раз подряд:
1. Amvera **автоматически перезагружает** контейнер
2. Если проблема persists — контейнер останется down
3. Проверьте логи для диагностики

---

## 💾 Database Backup Recommendations

### Current Setup (Amvera PostgreSQL)

На Amvera PostgreSQL, вероятно, уже есть автоматические бэкапы:

**Проверить бэкапы:**
1. **Amvera Console** → **Resources** → **Databases** → **reytingdb**
2. Ищите раздел "Backups" или "Snapshots"
3. Проверьте frequency и retention policy

### Backup Strategy

#### Option 1: Rely on Amvera (Simplest)
- ✅ Автоматические бэкапы (usually daily)
- ✅ Восстановление из консоли
- ❌ Нет контроля над schedule

#### Option 2: Manual Backups (Recommended)
Периодически создавать dump:

```bash
# Создать backup
pg_dump -h amvera-alex1976-cnpg-reyting-mo-rw \
        -U reyting_user \
        -d reytingdb \
        > reyting_backup_$(date +%Y%m%d_%H%M%S).sql

# Зипировать для экономии места
gzip reyting_backup_*.sql
```

#### Option 3: Automated Backups (Production)
Создать cronjob на локальном сервере или VM:

```bash
#!/bin/bash
# backup.sh - запускать через cron каждый день в 02:00

BACKUP_DIR="/path/to/backups"
DB_HOST="amvera-alex1976-cnpg-reyting-mo-rw"
DB_USER="reyting_user"
DB_NAME="reytingdb"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > \
  "$BACKUP_DIR/reyting_$(date +%Y%m%d_%H%M%S).sql.gz"

# Keep last 30 days only
find $BACKUP_DIR -name "reyting_*.sql.gz" -mtime +30 -delete

# Log
echo "Backup created: $(date)" >> /var/log/reyting_backup.log
```

**Crontab entry** (ежедневно в 02:00):
```
0 2 * * * /path/to/backup.sh
```

#### Option 4: AWS S3 Backups (Most Reliable)
Для очень надежного долгосрочного хранения:

```bash
#!/bin/bash
# s3_backup.sh

BACKUP_FILE="reyting_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > /tmp/$BACKUP_FILE

# Upload to S3
aws s3 cp /tmp/$BACKUP_FILE s3://your-bucket/reyting-backups/

# Cleanup
rm /tmp/$BACKUP_FILE
```

### Backup Retention Policy

| Type | Frequency | Retention |
|------|-----------|-----------|
| Daily | Every day 02:00 | 30 days |
| Weekly | Every Sunday | 3 months |
| Monthly | Last day of month | 1 year |

### Recovery Procedure

Если нужно восстановить данные из бэкапа:

```bash
# Загрузить backup в PostgreSQL
gunzip < reyting_backup_20251105_020000.sql.gz | \
  psql -h amvera-alex1976-cnpg-reyting-mo-rw \
       -U reyting_user \
       -d reytingdb

# Или создать новую БД из бэкапа
createdb -h amvera-alex1976-cnpg-reyting-mo-rw \
         -U reyting_user \
         reytingdb_restored

gunzip < reyting_backup_20251105_020000.sql.gz | \
  psql -h amvera-alex1976-cnpg-reyting-mo-rw \
       -U reyting_user \
       -d reytingdb_restored
```

---

## 📝 Request Logging

### Current Logging (Backend)

Backend логирует:
- Startup информацию
- CORS конфигурацию
- Database status
- Exception'ы

### Add Request Logging (Optional)

Для логирования всех API запросов, добавьте middleware в `backend/main.py`:

```python
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )
    return response
```

### View Logs in Amvera

1. **Applications** → **reyting** → **Logs**
2. Видите все логи в real-time
3. Можно скачать логи целиком

### Log Levels

- `INFO` - обычные операции
- `WARNING` - потенциальные проблемы
- `ERROR` - ошибки, требующие внимания
- `CRITICAL` - критические ошибки

---

## 🚨 Alerting & Monitoring

### Health Check Failures

Если `/health` падает:

1. **Amvera notices** (через 30+ секунд)
2. **Tries to restart** (до 3 раз)
3. **If still failing** → application marked as unhealthy
4. **Amvera notifies** (если настроены alerts)

### Setting Up Alerts in Amvera

1. **Applications** → **reyting** → **Notifications**
2. Добавить email или webhook для:
   - Health check failures
   - Deployment failures
   - Resource limits exceeded

### External Monitoring (Optional)

Для production можно использовать:

| Tool | Purpose | Cost |
|------|---------|------|
| Uptime Robot | Simple HTTP monitoring | Free |
| DataDog | Full APM & logs | Paid |
| New Relic | Performance monitoring | Paid |
| Grafana + Prometheus | Self-hosted monitoring | Free/Open Source |

Пример простого мониторинга:

```bash
#!/bin/bash
# monitor.sh - check health every minute

while true; do
  RESPONSE=$(curl -s https://reyting-alex1976.amvera.io/health)

  if [[ $RESPONSE == *"ok"* ]]; then
    echo "$(date) - Health: OK"
  else
    echo "$(date) - Health: FAILED"
    # Send alert (email, Slack, etc)
    # curl -X POST https://hooks.slack.com/... -d "API Down!"
  fi

  sleep 60
done
```

---

## 📈 Performance Monitoring

### Key Metrics to Monitor

1. **Response Time**
   - GET /api/rating should be < 500ms
   - If higher → add database indexes

2. **Error Rate**
   - Should be < 1%
   - Monitor for 5xx errors

3. **Database Connections**
   - SQLAlchemy pools (default 5 connections)
   - Monitor for connection pool exhaustion

4. **Memory Usage**
   - Container limit vs actual usage
   - Increase memory if OOMKilled

5. **Disk Space**
   - Log files growing?
   - Database size increasing normally?

### Database Performance Optimization (Future)

Когда будет достаточно данных, добавить индексы:

```sql
-- Frequently queried fields
CREATE INDEX idx_fact_indicator_mo_id ON fact_indicator(mo_id);
CREATE INDEX idx_fact_indicator_period_id ON fact_indicator(period_id);
CREATE INDEX idx_fact_indicator_ind_id ON fact_indicator(ind_id);

-- For searches
CREATE INDEX idx_dim_mo_name ON dim_mo(mo_name);
CREATE INDEX idx_dim_indicator_code ON dim_indicator(code);

-- Composite indexes for common queries
CREATE INDEX idx_fact_indicator_mo_period ON fact_indicator(mo_id, period_id);
CREATE INDEX idx_fact_summary_mo_period ON fact_summary(mo_id, period_id);
```

---

## 📋 Monitoring Checklist

### Daily
- [ ] Check Amvera dashboard for green statuses
- [ ] No error emails from health checks
- [ ] Application is responsive

### Weekly
- [ ] Review error logs
- [ ] Check response times
- [ ] Verify backups are created
- [ ] No disk space warnings

### Monthly
- [ ] Test backup restoration
- [ ] Review performance metrics
- [ ] Check for slow queries (if logging enabled)
- [ ] Update security patches (if applicable)

### Quarterly
- [ ] Review retention policies
- [ ] Plan capacity if needed
- [ ] Performance optimization review
- [ ] Security audit

---

## 🔧 Troubleshooting

### Health Check Failing

```
Issue: /health returns 500 or timeout
Possible causes:
1. Database connection lost
2. Memory exhausted
3. Disk full

Solution:
1. Check logs: Applications → Logs
2. Check database: psql -h ... -U ...
3. Restart: Applications → Redeploy
```

### High Response Times

```
Issue: API requests taking > 1 second
Possible causes:
1. Slow database queries
2. Missing indexes
3. Too many connections pooling

Solution:
1. Add database indexes
2. Increase memory
3. Enable query logging
```

### Out of Memory (OOMKilled)

```
Issue: Container keeps restarting
Error: OOMKilled

Solution:
1. Increase container memory (Amvera → Memory setting)
2. Check for memory leaks in code
3. Optimize database queries
```

---

## 📞 Support & Resources

- **Amvera Docs**: https://docs.amvera.ru/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Backup Tools**: pg_dump, pgbackrest, barman

---

**Версия**: 1.0
**Дата**: 05.11.2025
**Статус**: READY ✅

Следуйте этому руководству для надежной работы приложения в production!
