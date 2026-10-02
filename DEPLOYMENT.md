# Production Deployment Guide: AI Interview Answer Coach

This guide details the recommended architecture, environment configuration, database scaling trade-offs, and step-by-step deployment instructions for the **AI Interview Answer Coach** application.

---

## 1. Recommended Deployment Architecture

For a modern web application consisting of a React SPA frontend and a Python FastAPI backend with SQLite storage, the recommended deployment architecture decouples frontend edge hosting from backend API execution:

```
[ Client Browser ] 
       │
       ├──► (Static Assets & React App) ──────► Vercel / Netlify (Global Edge CDN)
       │                                              │
       └──► (REST API & AI Pipeline) ─────────► Render / Railway / Fly.io (FastAPI Backend)
                                                      │
                                                      ├──► Google Gemini API (AI Service)
                                                      └──► SQLite File Storage (interview_coach.db)
```

### Component Roles
1. **Frontend (Vercel / Netlify)**:
   - Serves static pre-built React HTML/CSS/JS assets via a global Edge CDN.
   - Handles route navigation client-side.
   - Reads backend URL from `VITE_BACKEND_URL`.

2. **Backend (Render / Railway / Fly.io)**:
   - Runs FastAPI web application with `gunicorn` worker processes.
   - Handles data validation, Gemini API integration, deterministic scoring, and technical verification.
   - Exposes operational health check at `/api/health`.

3. **Database (SQLite Initial Storage)**:
   - Stores interview sessions, questions, answers, and criteria breakdowns in a persistent file (`interview_coach.db`).

---

## 2. Database Trade-Offs: SQLite vs. Multi-User Scale

### Is SQLite Appropriate for Initial Deployment?
**Yes, for single-instance portfolio deployments.**
- **Zero Config Overhead**: Serverless file-based storage with no external database server administration required.
- **Fast Local Reads**: Database reads execute in-memory or via direct local disk IO with near-zero latency.
- **ACID Compliant**: Transactional guarantees for single-session writes.

### Scaling Limitations & Multi-User Alternatives
| Criteria | SQLite (Current Portfolio Setup) | PostgreSQL / Aurora (Production Scale) |
| :--- | :--- | :--- |
| **Concurrency** | SQLite locks the entire database file during writes (`SQLITE_BUSY` on concurrent writes). | PostgreSQL uses Row-Level Locking (MVCC), supporting thousands of concurrent write transactions. |
| **Horizontal Scaling** | Multiple web worker instances cannot share a local SQLite file without synchronization issues. | Multiple backend web nodes connect concurrently to a centralized database cluster. |
| **Backups & Disaster Recovery** | Requires periodic file copy snapshots. | Automated continuous point-in-time recovery (PITR) and replica failover. |

### Recommended Migration Path for High Scale
If scaling beyond single-instance deployment:
1. **Migrate Database**: Switch `DATABASE_URL` in [`backend/app/core/config.py`](file:///Users/yoshita/Desktop/AAI/backend/app/core/config.py) from SQLite to Managed PostgreSQL (`postgresql://user:password@host:5432/dbname`).
2. **Add Connection Pooling**: Enable SQLAlchemy connection pooling (`pool_size=10, max_overflow=20`).
3. **Add Caching**: Use Redis for caching recurring weakness stats or session state.

---

## 3. Production Environment Configurations

### A. Backend Production Environment Variables (`.env.production`)
Create these key-value pairs in your backend PaaS hosting dashboard (e.g. Render/Railway settings):

```env
ENVIRONMENT=production
PORT=8000
PROJECT_NAME="AI Interview Answer Coach"
GEMINI_API_KEY=AIzaSy_YOUR_ACTUAL_PRODUCTION_KEY_HERE
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./interview_coach.db
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
```

> ⚠️ **SECURITY REMINDER**: Never commit live API keys (`GEMINI_API_KEY`) to git repositories.

### B. Frontend Production Environment Variables (`.env.production`)
Create this key-value pair in your Vercel/Netlify project settings:

```env
VITE_BACKEND_URL=https://your-backend-api.onrender.com
```

---

## 4. Build & Startup Commands

### Backend Startup Commands
- **Install Dependencies**:
  ```bash
  pip install -r backend/requirements.txt
  ```

- **Production Server Startup (Gunicorn with Uvicorn ASGI Workers)**:
  ```bash
  gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  ```

### Frontend Build Commands
- **Install Dependencies**:
  ```bash
  npm install --prefix frontend
  ```

- **Production Static Bundle Build**:
  ```bash
  npm run build --prefix frontend
  ```
  *(Generates production assets in `frontend/dist/`)*

---

## 5. Health Check Verification

The backend exposes a lightweight health check endpoint for uptime monitoring tools (e.g. Better Uptime, UptimeRobot, or PaaS health probes):

- **Endpoint**: `GET /api/health`
- **Expected Status Code**: `200 OK`
- **Expected Payload**:
  ```json
  {
    "status": "healthy",
    "service": "AI Interview Answer Coach",
    "version": "1.0.0"
  }
  ```

---

## 6. Step-by-Step Deployment Instructions

### Step 1: Deploy Backend API (Render Example)
1. Push code repository to GitHub/GitLab.
2. Sign in to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your repository and configure:
   - **Name**: `ai-interview-coach-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` = `<your_api_key>`
   - `CORS_ORIGINS` = `https://<your-vercel-app-name>.vercel.app`
5. Click **Create Web Service**. Save your deployed URL (e.g. `https://ai-interview-coach-backend.onrender.com`).

### Step 2: Deploy Frontend SPA (Vercel Example)
1. Sign in to [Vercel Dashboard](https://vercel.com/) and click **Add New...** -> **Project**.
2. Import your code repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Expand **Environment Variables** and add:
   - `VITE_BACKEND_URL` = `https://ai-interview-coach-backend.onrender.com`
5. Click **Deploy**. Vercel will build and assign your live domain (e.g. `https://ai-interview-coach.vercel.app`).

### Step 3: Verify Live Deployment
1. Visit `https://<your-backend-api>.onrender.com/api/health` in your browser. Confirm HTTP status 200 and `"status": "healthy"`.
2. Open your live frontend app (`https://<your-vercel-app>.vercel.app`).
3. Submit a test interview answer under **Single Answer Analysis**.
4. Test **Interactive Interview Mode** (5-question session).
5. Verify **Progress & Weaknesses Tracker** tab aggregates database statistics correctly.
