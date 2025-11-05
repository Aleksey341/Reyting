# 🌐 Unified Frontend Deployment (Nginx Proxy Architecture)

**Status**: Ready for deployment
**Architecture**: Single frontend domain with Nginx reverse proxy to backend
**Last Updated**: 2025-11-05

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Browser User                                            │
│  https://reyting-frontend-alex1976.amvera.io/           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ (same-origin requests)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend Container (Nginx + React build)                │
│  ├─ Port 80 (internally)                                │
│  ├─ Serves: /  → React static files (dist/)             │
│  └─ Proxies: /api/* → backend                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ (HTTPS proxy, internal)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                       │
│  https://reyting-alex1976.amvera.io/api/                │
│  ├─ /api/health                                         │
│  ├─ /api/rating                                         │
│  └─ /api/...                                            │
└─────────────────────────────────────────────────────────┘
```

**Key Points:**
- ✅ User sees **one domain** (reyting-frontend-*.amvera.io)
- ✅ Same-origin requests (no CORS needed)
- ✅ Nginx transparently proxies /api to backend
- ✅ Independent frontend/backend deployment
- ✅ Both services can be updated separately

---

## 🔧 Configuration

### Frontend Build (.env.production)

```bash
# API endpoint during npm run build
VITE_API_BASE=/api

# This tells Vite to use relative /api path in built JavaScript
# At runtime, browser requests go to:
#   GET /api/health
#   GET /api/rating
#   etc.
```

### Nginx Proxy (nginx.conf)

```nginx
location /api/ {
  # Preserve original headers for backend
  proxy_set_header Host $host;                    # Client hostname
  proxy_set_header X-Real-IP $remote_addr;        # Client IP
  proxy_set_header X-Forwarded-For $remote_addr;  # For logging
  proxy_set_header X-Forwarded-Proto $scheme;     # For HTTPS detection

  # Forward to backend
  proxy_pass https://reyting-alex1976.amvera.io/api/;
  proxy_ssl_server_name on;                       # SNI for HTTPS

  # Allow large uploads
  client_max_body_size 50m;
}
```

---

## 🚀 Deployment Steps

### Step 1: Verify GitHub Changes

```bash
git log -1 --oneline
# Should show: "Refactor: Unified frontend via Nginx proxy"

git show --name-only
# Should show changes in:
#   - frontend/.env.production
#   - frontend/nginx.conf
```

### Step 2: Create/Configure Frontend App in Amvera

**Option A: Using Console UI**

1. Open Amvera console
2. Click "Create Application"
3. Select "Docker"
4. Fill in:
   ```
   Name: reyting-frontend
   Repository: https://github.com/Aleksey341/Reyting
   Branch: main

   Build Config:
   - Dockerfile: frontend/Dockerfile
   - Build context: . (root)
   - Build args: (none)

   Container:
   - Port: 80
   - Env vars: (none required - .env.production embedded in build)

   Domain: reyting-frontend-alex1976.amvera.io
   HTTPS: Enable (IMPORTANT!)
   ```

5. Click "Create"

**Option B: Using amvera-frontend.yml**

```bash
# Copy content and paste into Amvera console if it supports YAML
cat amvera-frontend.yml
```

### Step 3: Monitor Build

In Amvera console, watch build progress:
- [ ] Docker image building...
- [ ] `npm ci` installing dependencies
- [ ] `npm run build` creating dist/ folder
- [ ] Nginx config copied to image
- [ ] Image pushed successfully
- [ ] Container starting...
- [ ] Status: Running
- [ ] Health: Healthy

### Step 4: Enable HTTPS

**In Amvera console:**
1. Go to reyting-frontend app
2. Click "Domains"
3. For domain `reyting-frontend-alex1976.amvera.io`:
   - Toggle "HTTPS" to ON
   - Let's Encrypt will provision certificate (automatic)
   - Wait ~2 minutes for certificate issuance

### Step 5: Verify Deployment

Open in browser:
```
https://reyting-frontend-alex1976.amvera.io/
```

**Expected behavior:**
- ✅ Page loads (purple header visible)
- ✅ "Рейтинг эффективности" title
- ✅ "Проверка…" appears briefly
- ✅ Health badge shows "Бэкенд: OK" (green) within 2-3 seconds
- ✅ Data table loads with rating data
- ✅ Pagination buttons work
- ✅ No console errors (F12 → Console)
- ✅ No CORS errors (should be none!)

---

## 🔍 Verification Checklist

### Frontend Container

```bash
# Check container is running
curl -I https://reyting-frontend-alex1976.amvera.io/
# Should return 200 OK with HTML

# Check static assets load
curl -I https://reyting-frontend-alex1976.amvera.io/assets/index.*.js
# Should return 200 OK

# Check API proxy works
curl https://reyting-frontend-alex1976.amvera.io/api/health
# Should return: {"status":"ok","service":"reyting-api"}
```

### Browser DevTools (F12)

**Console tab:**
- [ ] No red errors
- [ ] No CORS errors
- [ ] Log message: "✓ Backend health check passed" (or error if backend down)

**Network tab (reload page):**
- [ ] `GET /` → 200 (HTML)
- [ ] `GET /assets/index.*.js` → 200 (JavaScript)
- [ ] `GET /api/health` → 200 (from proxy)
- [ ] `GET /api/rating?page=1&page_size=50` → 200 (data)

**Response size:**
- [ ] `index.*.js` should be < 50 KB (Vite optimized)
- [ ] Total bundle < 100 KB

---

## 🎯 Same-Origin Explanation

### Why This Matters

**Without Nginx proxy (❌ CORS problems):**
```
Browser (origin: reyting-frontend.amvera.io)
  → CORS preflight to backend.amvera.io
  → Backend must allow CORS
  → Adds latency (extra preflight requests)
  → CORS configuration complexity
```

**With Nginx proxy (✅ Same-origin):**
```
Browser (origin: reyting-frontend.amvera.io)
  → Request to reyting-frontend.amvera.io/api
  → Nginx receives request (same origin)
  → Nginx proxies to backend (internal, HTTPS)
  → No CORS needed!
  → No preflight latency
  → Backend CORS configuration optional
```

### Backend CORS Configuration

Since frontend accesses via Nginx proxy (same-origin), you can:

**Option 1: Remove CORS from backend**
```python
# Don't add CORSMiddleware if not needed
# Backend only accessible via Nginx proxy now
```

**Option 2: Keep CORS for direct API access**
```python
# Keep existing CORS config for development/testing
# Won't affect frontend (uses proxy)
```

---

## 🔄 Update Workflow

### Updating Frontend

```bash
# Make changes
git add .
git commit -m "Update frontend"
git push origin main

# In Amvera console:
# 1. Click reyting-frontend app
# 2. Click "Rebuild"
# 3. Wait for build to complete (2-3 minutes)
# 4. Service redeploys automatically
```

### Updating Backend

Backend deployment is completely independent:
```bash
# Changes to backend/ don't affect frontend build
# Backend continues running during frontend rebuild
# No downtime required!
```

---

## 🐛 Troubleshooting

### Issue: 499 Error

**Cause**: Frontend container not running or not on port 80

**Fix:**
1. Check Amvera console: Status should be "Running"
2. Check Container logs for errors
3. Verify `containerPort: 80` in amvera-frontend.yml
4. Rebuild if needed

### Issue: CORS Errors in Console

**Cause**: This should NOT happen with Nginx proxy!

**Check:**
1. Verify nginx.conf was copied to container
2. Check build logs for nginx.conf copy command
3. Verify /api location block exists in Nginx config
4. Restart container

### Issue: "Бэкенд: Error" (Red Badge)

**Cause**: Backend is not responding to Nginx proxy

**Check:**
1. Is backend running? `curl https://reyting-alex1976.amvera.io/api/health`
2. Check backend logs in Amvera console
3. Verify Nginx can reach backend (network connectivity)
4. Check backend CORS config allows Nginx requests

### Issue: 502 Bad Gateway

**Cause**: Nginx can't reach backend

**Check:**
1. Backend service running? (check Amvera console)
2. Backend domain name correct? (reyting-alex1976.amvera.io)
3. HTTPS certificate valid? (Let's Encrypt check)
4. Check Nginx error logs in container

### Issue: Empty Table (No Data)

**Cause**: Database not populated

**Check:**
1. Backend API returns data: `curl https://reyting-alex1976.amvera.io/api/rating`
2. If empty, load seed data: run `load_to_db_amvera.py` on backend
3. Check database connection in backend logs

---

## 📊 Performance Metrics

### Expected Response Times

```
GET /                    < 100ms  (HTML)
GET /assets/index.*.js   < 200ms  (JS, gzipped)
GET /api/health          < 300ms  (via proxy)
GET /api/rating          < 500ms  (via proxy, database query)
```

### Bundle Size

After `npm run build`:
```
dist/index.html          ~5 KB
dist/assets/index.*.js   ~40 KB (gzipped: ~12 KB)
dist/assets/style.*.css  ~15 KB (gzipped: ~3 KB)

Total: ~60 KB (gzipped: ~15 KB)
```

---

## 🔐 Security Notes

### Same-Origin Benefits

- ✅ No CORS preflight requests
- ✅ Credentials automatically included if set
- ✅ Simpler security model
- ✅ Backend doesn't expose CORS headers

### HTTPS Requirement

**IMPORTANT**: Both frontend and backend MUST be HTTPS:
- Frontend: Let's Encrypt (automatic in Amvera)
- Backend: Already using HTTPS (reyting-alex1976.amvera.io)

**Why**: Mixed HTTP/HTTPS causes browser warnings and potential issues

### Nginx Security

```nginx
# Current config includes:
✅ X-Forwarded-Proto header (HTTPS detection)
✅ X-Real-IP header (source IP logging)
✅ Host header preservation
✅ SSL SNI support
```

---

## 📝 Related Files

```
frontend/
├── .env.production          # VITE_API_BASE=/api
├── nginx.conf               # Reverse proxy configuration
├── Dockerfile               # Multi-stage build
├── package.json             # React + Vite dependencies
├── package-lock.json        # Locked versions
├── vite.config.ts           # Build configuration
├── index.html               # Entry point
└── src/
    ├── main.tsx             # React bootstrap
    ├── App.tsx              # Main component
    ├── api.ts               # Axios client (uses VITE_API_BASE)
    ├── styles.css           # Styling
    └── components/
        ├── HealthBadge.tsx  # Backend health check
        └── RatingTable.tsx  # Rating data display

amvera-frontend.yml         # Deployment configuration
```

---

## 🎓 Key Concepts

### How VITE_API_BASE Works

**Build time** (.env.production):
```
VITE_API_BASE=/api
```

**Compiled into JavaScript** (src/api.ts):
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
// At build time, this becomes:
// const API_BASE = '/api'
```

**Runtime** (browser):
```javascript
// Browser makes request to:
fetch('/api/health')
// Which is same-origin (same domain)
// Nginx receives it and proxies to backend
```

### Why Relative Path?

- ❌ Absolute: `https://reyting-alex1976.amvera.io/api` (hardcoded, CORS needed)
- ✅ Relative: `/api` (proxied by Nginx, same-origin)

---

## 📞 Support

If deployment fails:

1. **Check GitHub** - Latest commit: `git log -1`
2. **Check Amvera logs** - Build logs + Container logs
3. **Check file existence** - All required files present
4. **Check configuration** - All values correct
5. **Check permissions** - Image can access directories
6. **Check network** - Frontend can reach backend

See `FRONTEND_TROUBLESHOOTING.md` for detailed debugging.

---

**Version**: 1.0
**Status**: Tested and ready
**Architecture**: Nginx proxy (unified frontend, separate backend)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
