# 🔧 Frontend Troubleshooting Guide

**Status**: Updated after fix for 499 error
**Last Updated**: 2025-11-05
**Related Issues**: 499 Client Disconnect, Build Failures

---

## 🚨 Problem: 499 Error (Client Disconnected)

**What it means**: The frontend container is not running or not responding to requests.

### Root Cause (FOUND & FIXED)

The original `amvera-frontend.yml` had incorrect configuration:
```yaml
# ❌ WRONG - told Amvera to:
containerPort: 3000      # But Nginx listens on 80
command: [serve, ...]    # But image has Nginx, not serve
```

### Solution Applied

✅ Fixed `amvera-frontend.yml`:
```yaml
# ✅ CORRECT - now tells Amvera:
containerPort: 80        # Nginx listens on 80
# No command - uses Dockerfile CMD (Nginx)
```

✅ Added missing `package-lock.json` for reproducible Docker builds

---

## 📋 Pre-Deployment Checklist

### File Verification

```bash
# Check all required files exist
cd frontend/

# Build files
ls -la Dockerfile          # ✓ Multi-stage build
ls -la nginx.conf          # ✓ Reverse proxy config
ls -la vite.config.ts      # ✓ Vite configuration

# Source code
ls -la src/
  ls -la src/main.tsx      # ✓ React entry point
  ls -la src/App.tsx       # ✓ Main app component
  ls -la src/api.ts        # ✓ Axios client
  ls -la src/styles.css    # ✓ Styling
  ls -la src/components/   # ✓ HealthBadge.tsx, RatingTable.tsx

# Dependencies
ls -la package.json        # ✓ Minimal dependencies
ls -la package-lock.json   # ✓ Locked versions (NEW)

# Config files
ls -la index.html          # ✓ HTML entry point
```

### Configuration Verification

```bash
# Check Dockerfile is correct
grep "FROM nginx:alpine" Dockerfile              # ✓ Should exist
grep "COPY nginx.conf" Dockerfile                # ✓ Should copy config
grep "COPY --from=build /app/dist" Dockerfile    # ✓ Should copy dist/

# Check nginx.conf is correct
grep "listen 80" nginx.conf                      # ✓ Nginx on port 80
grep "proxy_pass https://reyting-alex1976" nginx.conf  # ✓ Backend proxy
grep "try_files.*index.html" nginx.conf          # ✓ SPA routing

# Check vite.config.ts
grep "outDir: 'dist'" vite.config.ts             # ✓ Output to dist/
```

---

## 🔨 Local Build Test (Before Amvera)

If you have Docker installed locally:

```bash
# Navigate to project root
cd path/to/project

# Build Docker image
docker build -f frontend/Dockerfile -t reyting-frontend:test .

# Run locally
docker run -p 8080:80 reyting-frontend:test

# Test in browser
# http://localhost:8080/
# Should show purple header, "Рейтинг эффективности", loading spinner
```

**Expected output:**
```
Step 1/8 : FROM node:20-alpine AS build
Step 2/8 : WORKDIR /app
Step 3/8 : COPY package.json package-lock.json* ./
Step 4/8 : RUN npm ci
Step 5/8 : COPY . .
Step 6/8 : RUN npm run build
Step 7/8 : FROM nginx:alpine
Step 8/8 : COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**If build fails on Step 4 (npm ci)**:
- Means package-lock.json is missing or corrupted
- Check: `ls -la package-lock.json`
- Fix: Re-add package-lock.json from GitHub

---

## 🌐 Deployment Steps in Amvera Console

### Step 1: Navigate to Amvera UI
1. Open https://console.amvera.io/
2. Find service: **reyting-frontend**
3. Click service name

### Step 2: Trigger Rebuild
1. Click **"Rebuild Application"** (or similar button)
2. Confirm: "Are you sure?"
3. Wait for build to complete

### Step 3: Monitor Build Progress
Watch for:
- ✅ `Build started`
- ✅ `Docker image building...`
- ✅ `npm ci` completed
- ✅ `npm run build` completed (should create dist/)
- ✅ `Docker image pushed`
- ✅ `Build successful`

**If build fails:**
See "Common Build Errors" section below.

### Step 4: Check Container Status
In Amvera console:
- `Status: Running` ✅
- `Health: Healthy` ✅
- Port: 80 ✅

### Step 5: Test Frontend
Open in browser:
```
https://reyting-frontend-alex1976.amvera.io/
```

**Expected:**
- Purple gradient header loads
- "Рейтинг эффективности" title visible
- "Проверка…" (loading) badge appears
- Within 2-3 seconds: either "Бэкенд: OK" (green) or "Бэкенд: Error" (red)

---

## 🐛 Common Issues & Fixes

### Issue 1: 499 Client Disconnected

**Symptoms:**
```
GET https://reyting-frontend-alex1976.amvera.io/ 499
```

**Causes & Solutions:**

**Cause A: Old amvera-frontend.yml configuration**
- **Fix**: Update from GitHub
  ```bash
  git pull origin main
  ```
  Ensures you have latest amvera-frontend.yml with `containerPort: 80`

**Cause B: Container not running**
- **Check**: Amvera console → reyting-frontend → Status
- **If crashed**: Click "Logs" button
  - Look for nginx startup errors
  - Look for dist/ not found errors
- **Fix**: Rebuild application

**Cause C: Nginx config not copied**
- **Check in logs**: Would see "nginx: [error] open() '/etc/nginx/conf.d/default.conf' failed"
- **Fix**: Ensure `COPY nginx.conf /etc/nginx/conf.d/default.conf` in Dockerfile

---

### Issue 2: Build Fails at npm ci

**Error in build logs:**
```
E: npm ERR! code ERESOLVE
E: npm ERR! ERESOLVE unable to resolve dependency tree
```

**Cause**: package-lock.json corrupted or has wrong versions

**Fix**:
```bash
# Delete local package-lock.json
rm frontend/package-lock.json

# Regenerate from package.json
cd frontend
npm install --package-lock-only

# Commit
git add package-lock.json
git commit -m "Regenerate package-lock.json"
git push
```

Then rebuild in Amvera.

---

### Issue 3: 502 Bad Gateway or Backend Error Badge (Red)

**Symptoms:**
- Frontend loads (header visible)
- Badge shows "Бэкенд: Error" (red)
- OR Nginx shows 502/503 errors

**Cause**: Backend is not accessible or not running

**Check backend:**
```bash
curl https://reyting-alex1976.amvera.io/health
```

Should respond with:
```json
{"status":"ok","service":"reyting-api"}
```

**If it fails:**
1. Check backend service status in Amvera console
2. Verify backend domain: `reyting-alex1976.amvera.io`
3. Check backend logs for errors
4. Ensure DATABASE_URL env var is set in backend

**Why frontend still works but shows red badge:**
- Frontend serves HTML/JS fine (Nginx is working)
- But API proxy fails (backend unavailable)
- This is expected! Backend and frontend are separate services

---

### Issue 4: Empty Table (No Data Rows)

**Symptoms:**
- Frontend loads
- Header visible
- Badge shows "Бэкенд: OK" (green)
- But table is empty: "Нет данных"

**Cause**: Database not populated with data

**Check:**
```bash
# Get rating data via API
curl https://reyting-alex1976.amvera.io/api/rating?page=1&page_size=10
```

Should return:
```json
{
  "data": [
    {"mo_id": 1, "mo_name": "Липецк", "score_total": 95.5, ...},
    ...
  ]
}
```

If `"data": []` - database is empty.

**Fix**: Load seed data
1. SSH to Amvera backend container
2. Run: `python load_to_db_amvera.py`
3. Or manually insert test data via SQL

---

### Issue 5: CORS Errors in Browser Console

**Error:**
```
Access to XMLHttpRequest at 'https://reyting-alex1976.amvera.io/api/...'
from origin 'https://reyting-frontend-alex1976.amvera.io'
blocked by CORS policy
```

**This should NOT happen!**

**Why?** Nginx reverse proxy handles all requests:
- Browser → Nginx (same domain)
- Nginx → Backend (internal)
- No CORS needed!

**If you see this error:**
- **Check**: Is frontend really using Nginx proxy?
- **Fix**: Verify nginx.conf was copied to container
- **Debug**: Check frontend build logs for warnings

---

### Issue 6: 404 on Page Refresh

**Symptoms:**
- Frontend loads fine (localhost:80/)
- Clicking "Следующая" button works
- But refreshing page shows 404

**This should NOT happen!**

**Why?** `try_files $uri /index.html` should handle this

**Fix**: Verify nginx.conf has:
```nginx
location / {
  try_files $uri /index.html;
}
```

If missing, rebuild from GitHub.

---

## 📊 Performance Check

### Response Times

Test API response time through proxy:

```bash
# Health check
time curl https://reyting-frontend-alex1976.amvera.io/api/health

# Expected: < 200ms
# If > 1s: backend may be slow or network issues
```

### Browser DevTools Check

1. Open DevTools (F12)
2. Network tab
3. Reload page
4. Check request timing:
   - `GET /` (HTML) - should be < 100ms
   - `GET /assets/*.js` - should be < 500ms
   - `GET /api/health` - should be < 200ms
   - `GET /api/rating` - should be < 500ms

### Bundle Size

After build, check size:
```bash
# This is in dist/ after npm run build
du -sh dist/
# Should be < 100KB for Vite + React minimal setup
```

---

## 🔍 Debugging in Amvera

### View Container Logs

In Amvera console:
1. Click service → "Logs" button
2. View real-time output
3. Look for errors starting with `nginx:` or `Error:`

### Common log messages:

```
# Good signs:
"nginx: master process started"
"Listening on [::]:80"

# Bad signs:
"nginx: [error] open() ... failed"
"ENOENT: no such file or directory, open '/app/dist'"
"cannot assign requested address"
```

### SSH to Container (if available)

```bash
# Connect to container
ssh user@reyting-frontend-alex1976.amvera.io

# Check Nginx is running
ps aux | grep nginx

# Check files are in place
ls -la /usr/share/nginx/html/
ls -la /etc/nginx/conf.d/default.conf

# Test Nginx config
nginx -t

# View Nginx error log
tail -50 /var/log/nginx/error.log
```

---

## ✅ Verification Checklist

### After Deployment

- [ ] Amvera console shows Status: Running
- [ ] Amvera console shows Health: Healthy
- [ ] No errors in container logs
- [ ] Can access https://reyting-frontend-alex1976.amvera.io/
- [ ] Page loads (purple header visible)
- [ ] Health badge shows (green or red)
- [ ] No 404/502/503 errors in Network tab

### After Backend Connection

- [ ] Health badge is green ("Бэкенд: OK")
- [ ] Table loads with data rows
- [ ] Pagination buttons work
- [ ] Scores display correctly
- [ ] No CORS errors in console

### Production Ready

- [ ] Bundle size < 100KB
- [ ] Page load < 2 seconds
- [ ] API responses < 500ms
- [ ] No console errors
- [ ] Responsive design works (F12 → toggle device toolbar)

---

## 🚀 If All Else Fails

### Nuclear Option: Complete Rebuild

```bash
# 1. In your local machine
cd path/to/project

# Clean everything
rm -rf frontend/node_modules frontend/dist

# 2. Ensure files are correct
git status
git log -1 --oneline
# Should show commit with package-lock.json

# 3. If something is wrong, reset and pull
git reset --hard
git pull origin main

# 4. Push to GitHub if you made local changes
git add .
git commit -m "Rebuild frontend"
git push

# 5. In Amvera console
# Click "Rebuild Application"
# Wait 5-10 minutes for complete rebuild
```

### Contact Support

If still failing after checklist, provide:
1. Latest commit hash: `git log -1 --oneline`
2. Build logs from Amvera console (copy full text)
3. Container logs from Amvera console (last 50 lines)
4. Browser DevTools Network tab screenshot
5. What you expected vs what happened

---

## 📚 Reference Files

**Key files for frontend deployment:**
- `amvera-frontend.yml` - Deployment configuration (root level)
- `frontend/Dockerfile` - Multi-stage build with Nginx
- `frontend/nginx.conf` - Reverse proxy configuration
- `frontend/package.json` - Dependencies (minimal)
- `frontend/package-lock.json` - Locked versions (reproducible builds)
- `frontend/vite.config.ts` - Build configuration
- `frontend/index.html` - HTML entry point
- `frontend/src/main.tsx` - React entry point

**Related documentation:**
- `TWO_SERVICE_DEPLOYMENT_GUIDE.md` - Backend + Frontend architecture
- `VITE_MIGRATION.md` - Why we use Vite instead of Create React App
- `PERFORMANCE_OPTIMIZATION.md` - Optimization strategies

---

**Version**: 2.0
**Status**: Tested & Updated
**Last Fix**: Added package-lock.json, fixed amvera-frontend.yml port

🤖 Generated with [Claude Code](https://claude.com/claude-code)
