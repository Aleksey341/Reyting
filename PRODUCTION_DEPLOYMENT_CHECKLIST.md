# 🚀 Production Deployment Checklist

Полный чек-лист для развертывания Reyting Dashboard на Amvera (backend + frontend).

---

## 📋 Pre-Deployment (локально)

### Frontend Build
- [ ] Проверить что `frontend/.env.production` содержит правильный API URL
  ```
  VITE_API_BASE=https://reyting-alex1976.amvera.io/api
  ```
- [ ] Локально собрать frontend: `cd frontend && npm ci && npm run build`
- [ ] Проверить что `dist/` папка создана и содержит файлы
- [ ] Проверить что `dist/index.html` существует

### Backend Config
- [ ] Проверить что `backend/main.py` содержит CORS конфигурацию
- [ ] Убедиться что `ALLOWED_ORIGINS` включает оба домена:
  - `https://reyting-frontend-alex1976.amvera.io`
  - `https://reyting-alex1976.amvera.io`

### Database
- [ ] Проверить что seed данные загружены: `SELECT COUNT(*) FROM dim_mo;`
- [ ] Проверить что таблицы существуют и заполнены

---

## 🔧 Amvera Backend Configuration

### Backend Service (reyting)

#### 1. Basic Setup
- [ ] Application name: `reyting`
- [ ] Repository: `https://github.com/Aleksey341/Reyting`
- [ ] Branch: `main`
- [ ] Dockerfile: `Dockerfile` (корневой)

#### 2. Build Configuration
- [ ] Dockerfile path: `Dockerfile`
- [ ] Build context: `/` (default)

#### 3. Runtime Configuration
- [ ] Container port: `80`
- [ ] Command: Default (используется CMD из Dockerfile)
- [ ] Memory: `512 MB` (или больше)
- [ ] CPU: `100m` (или больше)

#### 4. Environment Variables (важно!)
```
DATABASE_URL = postgresql://reyting_user:Qwerty12345@amvera-alex1976-cnpg-reyting-mo-rw:5432/reytingdb

DEBUG = false

ALLOWED_ORIGINS = https://reyting-frontend-alex1976.amvera.io,https://reyting-alex1976.amvera.io
```

#### 5. Domains
- [ ] Host: `reyting-alex1976.amvera.io` (ваш домен)
- [ ] Routes: `/` → port `80`
- [ ] Type: `HTTPS`
- [ ] Enable: `Принудительный HTTPS` (redirect HTTP → HTTPS)

#### 6. Deploy
- [ ] Нажать **Deploy** и дождаться успешной сборки (2-5 минут)

#### 7. Verification
- [ ] Откройте в браузере: `https://reyting-alex1976.amvera.io/health`
  - Должен вернуть: `{"status": "ok", "service": "reyting-api"}`
- [ ] Откройте: `https://reyting-alex1976.amvera.io/api/docs`
  - Должен загрузиться Swagger UI
- [ ] Откройте: `https://reyting-alex1976.amvera.io/api`
  - Должен вернуть JSON с информацией об API

---

## 🎨 Amvera Frontend Configuration

### Frontend Service (reyting-frontend)

#### 1. Basic Setup
- [ ] Application name: `reyting-frontend`
- [ ] Repository: `https://github.com/Aleksey341/Reyting` (тот же репо)
- [ ] Branch: `main`
- [ ] Dockerfile: `frontend/Dockerfile`

#### 2. Build Configuration
- [ ] Dockerfile path: `frontend/Dockerfile`
- [ ] Build context: `/` (default)

#### 3. Runtime Configuration
- [ ] Container port: `3000`
- [ ] Memory: `256 MB`
- [ ] CPU: `50m`

#### 4. Environment Variables (опционально)
```
# Если нужно переопределить в runtime
VITE_API_BASE = https://reyting-alex1976.amvera.io/api
```

#### 5. Domains
- [ ] Host: `reyting-frontend-alex1976.amvera.io` (ваш фронтенд домен)
- [ ] Routes: `/` → port `3000`
- [ ] Type: `HTTPS`
- [ ] Enable: `Принудительный HTTPS` (redirect HTTP → HTTPS)

#### 6. Deploy
- [ ] Нажать **Deploy** и дождаться успешной сборки (3-5 минут)
- [ ] **Важно**: Сборка фронтенда включает `npm run build`, что использует переменные из `.env.production`

#### 7. Verification
- [ ] Откройте в браузере: `https://reyting-frontend-alex1976.amvera.io/`
  - Должна загрузиться HTML страница дашборда
- [ ] DevTools → Network → проверить что нет 404 или CORS ошибок
- [ ] DevTools → Console → должны видеть:
  ```
  [API] Initialized with base URL: https://reyting-alex1976.amvera.io/api
  ```

---

## 🔐 HTTPS Setup

### Для Backend
- [ ] Applications → reyting → Domains
- [ ] Нажать карандаш рядом с доменом
- [ ] Выбрать `HTTPS`
- [ ] Включить `Принудительный HTTPS`
- [ ] Применить
- [ ] Подождать 5-15 минут на выпуск Let's Encrypt сертификата
- [ ] Проверить статус: должен быть `✓ Активен`

### Для Frontend
- [ ] Applications → reyting-frontend → Domains
- [ ] Нажать карандаш рядом с доменом
- [ ] Выбрать `HTTPS`
- [ ] Включить `Принудительный HTTPS`
- [ ] Применить
- [ ] Подождать 5-15 минут
- [ ] Проверить статус: должен быть `✓ Активен`

---

## ✅ Post-Deployment Verification

### Backend Health Checks

```bash
# Health check
curl https://reyting-alex1976.amvera.io/health
# Ожидается: {"status": "ok", "service": "reyting-api"}

# API info
curl https://reyting-alex1976.amvera.io/api | jq
# Ожидается: JSON с endpoints и информацией

# API docs
curl -I https://reyting-alex1976.amvera.io/api/docs
# Ожидается: 200 OK
```

### Frontend Health Checks

```bash
# Frontend page
curl -I https://reyting-frontend-alex1976.amvera.io/
# Ожидается: 200 OK

# Check that page loads
curl https://reyting-frontend-alex1976.amvera.io/ | grep -c "root"
# Ожидается: найти элемент <div id="root">
```

### Browser Verification

1. **Открыть Frontend**:
   - [ ] `https://reyting-frontend-alex1976.amvera.io/`
   - [ ] Страница должна загрузиться без ошибок
   - [ ] Должны видеться компоненты дашборда

2. **DevTools → Network**:
   - [ ] Нет 404 ошибок на файлах
   - [ ] Нет CORS ошибок в API запросах
   - [ ] API запросы идут на `https://reyting-alex1976.amvera.io/api/*`
   - [ ] Все запросы возвращают 200 (или 304 для кэшированных)

3. **DevTools → Console**:
   - [ ] Нет красных ошибок
   - [ ] Видны логи инициализации API
   - [ ] Видны логи API запросов и ответов

4. **Функциональность**:
   - [ ] Дашборд отображает данные (если seed данные загружены)
   - [ ] Можно переходить между страницами (Rating, Map, Analytics)
   - [ ] Фильтры работают (если реализованы)

---

## 🐛 Troubleshooting

### Backend недоступен (499/503)

```bash
# Проверить логи
Applications → reyting → Logs
# Ищите ошибки подключения к БД или startup ошибки

# Проверить переменные окружения
Applications → reyting → Переменные
# Убедитесь что DATABASE_URL правильный

# Перестартовать приложение
Applications → reyting → Redeploy
```

### Frontend не загружается (404/499)

```bash
# Проверить логи сборки
Applications → reyting-frontend → Logs
# Ищите ошибки npm install или npm run build

# Проверить что dist/ создана
# (должно быть видно в логах: "dist/" или "build output to dist/")

# Перестартовать приложение
Applications → reyting-frontend → Redeploy
```

### CORS ошибки

```bash
# Проверить ALLOWED_ORIGINS в backend
Applications → reyting → Переменные
# Должно содержать: https://reyting-frontend-alex1976.amvera.io

# Перестартовать backend после изменения
Applications → reyting → Redeploy

# Проверить в DevTools Console
# Должно быть: Access-Control-Allow-Origin: https://reyting-frontend-...
```

### API возвращает пусто

```bash
# Проверить что seed данные загружены
psql -h amvera-alex1976-cnpg-reyting-mo-rw \
     -U reyting_user \
     -d reytingdb \
     -p 5432

psycopg2# SELECT COUNT(*) FROM dim_mo;
# Должно быть > 0

# Если пусто - загрузить seed данные
psycopg2# \i etl/seed_minimal_data.sql
```

### Сертификат не выпустился

```bash
# Способ 1: Toggle HTTP/HTTPS
Applications → Домены
Нажать карандаш → HTTP → Применить
Подождать 10 сек
Нажать карандаш → HTTPS → Применить
Подождать 5-15 минут

# Способ 2: Пересоздать домен
Applications → Домены
Удалить старый домен
Добавить заново
Повторить шаги HTTPS Setup
```

---

## 📊 Final Verification Table

| Item | Check | Status |
|------|-------|--------|
| Backend runs | `curl https://backend/health` | ✓ 200 OK |
| Backend API accessible | `curl https://backend/api` | ✓ 200 OK |
| Frontend runs | `curl https://frontend/` | ✓ 200 OK |
| Backend HTTPS | Browser shows no warnings | ✓ OK |
| Frontend HTTPS | Browser shows no warnings | ✓ OK |
| CORS working | DevTools → no CORS errors | ✓ OK |
| API calls succeed | DevTools → /api/* returns 200 | ✓ OK |
| Frontend loads data | Page shows content | ✓ OK |
| Database populated | SELECT COUNT(*) FROM dim_mo | ✓ > 0 |

---

## 🎯 Success Criteria

✅ **Deployment считается успешным когда:**

1. Backend доступен по HTTPS с валидным сертификатом
2. Frontend доступен по HTTPS с валидным сертификатом
3. Frontend загружается без 404 ошибок
4. API запросы с фронтенда успешны (200, не 403/CORS)
5. DevTools Console не показывает ошибок
6. Дашборд отображает данные из API

---

## 📞 Контакты

- **Amvera Support**: https://amvera.ru/support/
- **GitHub Repository**: https://github.com/Aleksey341/Reyting
- **API Docs**: `https://reyting-alex1976.amvera.io/api/docs`

---

**Версия**: 1.0
**Дата**: 05.11.2025
**Статус**: READY FOR DEPLOYMENT ✅
