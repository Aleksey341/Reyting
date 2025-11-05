# 🚀 Two-Service Deployment Guide: Backend + Frontend

This guide explains how to deploy Reyting Dashboard as two independent services on Amvera:
- **Backend**: FastAPI on port 80, API endpoints on `/api`
- **Frontend**: React/Vite on port 3000, communicates with backend via CORS

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│          Amvera Platform               │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐  ┌─────────────┐ │
│  │  Backend Service │  │  Frontend   │ │
│  │  (reyting)       │  │  Service    │ │
│  ├──────────────────┤  ├─────────────┤ │
│  │ Port: 80         │  │ Port: 3000  │ │
│  │ Domain: .../api  │  │ Domain: ... │ │
│  └──────────────────┘  └─────────────┘ │
│        │                      │         │
│        └──────────────────────┘         │
│          CORS enabled                   │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  PostgreSQL (shared database)    │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📋 Prerequisites

1. **GitHub Repository**: https://github.com/Aleksey341/Reyting
2. **Amvera Account**: With access to create multiple applications
3. **Database**: PostgreSQL 15 on Amvera (already set up)
4. **Domains**: Two subdomains available (or Amvera-generated domains)

---

## 🔧 Step 1: Deploy Backend (API Service)

### 1.1 Create Backend Application in Amvera

1. Go to Amvera Console → **Applications** → **Create**
2. Choose **"From repository"**
3. Select: `https://github.com/Aleksey341/Reyting`
4. Choose branch: `main`

### 1.2 Configure Backend Build

**In Configuration → Build:**
- **Dockerfile**: `Dockerfile` (the root-level one we created)
- **Build context**: `/` (default)

### 1.3 Configure Backend Runtime

**In Configuration → Run:**
- **Container port**: `80`
- **Command**: Leave default (uses CMD from Dockerfile)
- **Memory**: `512 MB` (or adjust as needed)
- **CPU**: `100m` (or adjust)

### 1.4 Configure Backend Environment Variables

**In Variables:**
```
DATABASE_URL = postgresql://reyting_user:Qwerty12345@amvera-alex1976-cnpg-reyting-mo-rw:5432/reytingdb

DEBUG = false

ALLOWED_ORIGINS = https://reyting-frontend-alex1976.amvera.io,http://localhost:3000
```

(Replace `reyting-frontend-alex1976.amvera.io` with your actual frontend domain)

### 1.5 Configure Backend Domain

**In Domains:**
- **Host**: `reyting-alex1976.amvera.io` (or your domain)
- **Routes**: `/` → port `80`

### 1.6 Deploy Backend

Click **Deploy** and wait for build to complete (~2-3 minutes)

**Verify Backend is Running:**
```bash
# Health check
curl https://reyting-alex1976.amvera.io/health
# Should return: {"status": "ok", "service": "reyting-api"}

# API info
curl https://reyting-alex1976.amvera.io/api | jq
# Should return JSON with endpoints list

# Swagger docs
https://reyting-alex1976.amvera.io/api/docs
```

---

## 🎨 Step 2: Deploy Frontend (UI Service)

### 2.1 Create Frontend Application in Amvera

1. Go to Amvera Console → **Applications** → **Create**
2. Choose **"From repository"**
3. Select: `https://github.com/Aleksey341/Reyting` (same repo)
4. Choose branch: `main`

### 2.2 Configure Frontend Build

**In Configuration → Build:**
- **Dockerfile**: `frontend/Dockerfile`
- **Build context**: `/` (default)

### 2.3 Configure Frontend Runtime

**In Configuration → Run:**
- **Container port**: `3000`
- **Memory**: `256 MB`
- **CPU**: `50m`

### 2.4 Configure Frontend Environment Variables

**In Variables:**
```
VITE_API_BASE = https://reyting-alex1976.amvera.io/api

VITE_APP_TITLE = Reyting Dashboard

VITE_DEBUG = false
```

(Replace `reyting-alex1976.amvera.io` with your backend domain)

### 2.5 Configure Frontend Domain

**In Domains:**
- **Host**: `reyting-frontend-alex1976.amvera.io` (or your domain)
- **Routes**: `/` → port `3000`

### 2.6 Deploy Frontend

Click **Deploy** and wait for build to complete (~2-3 minutes)

**Verify Frontend is Running:**
```bash
# Check if frontend loads
curl https://reyting-frontend-alex1976.amvera.io/
# Should return HTML

# Check in browser
https://reyting-frontend-alex1976.amvera.io/
```

---

## ✅ Step 3: Verify Communication Between Services

### 3.1 Check CORS Headers

In browser DevTools → Network tab, check a request to `/api/rating`:
- **Request Origin**: `https://reyting-frontend-alex1976.amvera.io`
- **Response Headers** should include:
  - `Access-Control-Allow-Origin: https://reyting-frontend-alex1976.amvera.io`
  - `Access-Control-Allow-Methods: *`
  - `Access-Control-Allow-Headers: *`

### 3.2 Check API Calls in Browser Console

Open browser DevTools → Console tab:
- Look for `[API] Initialized with base URL: https://reyting-alex1976.amvera.io/api`
- Watch `[API Request]` and `[API Response]` logs
- No CORS errors should appear

### 3.3 Test API Endpoints

```bash
# From frontend, API should return data
curl -H "Origin: https://reyting-frontend-alex1976.amvera.io" \
     https://reyting-alex1976.amvera.io/api/rating

# Should return JSON array with rating data (or empty if no seed data loaded)
```

---

## 🌱 Step 4: Load Seed Data

If you haven't loaded seed data yet:

```bash
psql -h amvera-alex1976-cnpg-reyting-mo-rw \
     -U reyting_user \
     -d reytingdb \
     -p 5432

# Enter password: Qwerty12345
# Then in psql:
\i etl/seed_minimal_data.sql
\q
```

After seed data is loaded, `/api/rating` should return sample records.

---

## 🔍 Troubleshooting

### Frontend loads but API calls fail (CORS error)

**Symptom**: Browser console shows `Access to XMLHttpRequest at 'https://backend/api/...' from origin 'https://frontend/...' has been blocked by CORS policy`

**Solution**:
1. Verify frontend domain is in backend's `ALLOWED_ORIGINS` env var
2. Restart backend service: Application → **Redeploy**
3. Check backend logs for CORS configuration

### Frontend shows blank/loading forever

**Symptom**: Page loads but no content appears, browser console shows network errors

**Solution**:
1. Check `VITE_API_BASE` env var in frontend configuration
2. Verify it matches your backend domain exactly (https, no trailing slash)
3. Restart frontend: Application → **Redeploy**
4. Open browser DevTools → check Console for API initialization message

### API returns 404 on /api endpoints

**Symptom**: `curl https://backend/api/rating` returns 404

**Solution**:
1. Check backend is running: `curl https://backend/health` should return 200
2. Verify routes are included in `backend/main.py`
3. Check logs: Application → **Logs** → look for route registration messages

### Database connection fails

**Symptom**: Backend logs show `could not connect to server`

**Solution**:
1. Verify `DATABASE_URL` env var is correct
2. Check password: `Qwerty12345`
3. Check host: `amvera-alex1976-cnpg-reyting-mo-rw`
4. Verify database exists and is accessible
5. Restart backend service

---

## 📊 Monitoring

### View Logs

**Backend Logs:**
- Application → reyting → **Logs**
- Look for startup messages and request logs

**Frontend Logs:**
- Application → reyting-frontend → **Logs**
- Look for build output and runtime errors

### Check Health

Both services have health checks configured:
- **Backend**: GET `/health` (checked every 30s)
- **Frontend**: GET `/` (checked every 30s)

If health check fails 3 times, Amvera will restart the service.

### Monitor Requests

In browser DevTools:
- **Network tab**: See all API requests and responses
- **Console tab**: See API client logs with `[API]` prefix

---

## 🚀 Scaling and Updates

### Update Backend Code

1. Commit changes to `backend/` or root `Dockerfile`
2. Push to GitHub main branch
3. In Amvera: Application → reyting → **Deploy**

### Update Frontend Code

1. Commit changes to `frontend/` or `frontend/Dockerfile`
2. Push to GitHub main branch
3. In Amvera: Application → reyting-frontend → **Deploy**

**Note**: You can deploy backend and frontend independently — they don't depend on each other (except via API).

---

## 🔒 Security Considerations

- **ALLOWED_ORIGINS**: Restrict to your frontend domain (not `*` in production)
- **DEBUG**: Keep `false` in production
- **DATABASE_URL**: Keep in secrets/env, never commit to git
- **CORS**: Frontend domain should be HTTPS in production

---

## 📝 Configuration Reference

### Backend (amvera-backend.yml)

```yaml
app:
  name: reyting
  build:
    dockerfile: Dockerfile
  run:
    containerPort: 80
    env:
      - name: DATABASE_URL
        value: postgresql://reyting_user:...
      - name: ALLOWED_ORIGINS
        value: https://frontend-domain
```

### Frontend (amvera-frontend.yml)

```yaml
app:
  name: reyting-frontend
  build:
    dockerfile: frontend/Dockerfile
  run:
    containerPort: 3000
    env:
      - name: VITE_API_BASE
        value: https://backend-domain/api
```

---

## 🎉 Success Checklist

- [x] Backend deployed and `/health` returns 200
- [x] Backend `/api/docs` is accessible
- [x] Frontend deployed and page loads
- [x] Frontend can reach `/api/rating` without CORS errors
- [x] API returns data (seed data loaded)
- [x] Health checks passing for both services
- [x] Browser DevTools shows successful API requests

---

**Version**: 1.0
**Date**: 05.11.2025
**Status**: READY FOR DEPLOYMENT ✅

For questions or issues, check the application logs in Amvera Console.
