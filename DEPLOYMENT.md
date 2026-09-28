# PRAYAAS Production Deployment Guide: Render (Backend) & Vercel (Frontend)

This guide walks you through deploying the complete PRAYAAS Geospatial Intelligence platform to **Render** (FastAPI + PostGIS) and **Vercel** (Vite + React GIS Workstation).

---

## Architecture Overview

```
┌─────────────────────────────────┐           ┌───────────────────────────────────┐
│         VERCEL FRONTEND         │           │          RENDER BACKEND           │
│  Vite + React + Leaflet         │           │  FastAPI + GeoAlchemy2            │
│  URL: https://prayaas.vercel.app│──(HTTPS)─▶│  URL: https://prayaas.onrender.com│
└─────────────────────────────────┘           └─────────────────┬─────────────────┘
                                                                │ (PostgreSQL)
                                              ┌─────────────────▼─────────────────┐
                                              │      RENDER POSTGIS DATABASE      │
                                              │  PostgreSQL 16 + PostGIS 3.4      │
                                              │  Tables: habitations, zones, etc. │
                                              └───────────────────────────────────┘
```

---

## Step 1: Push Repository to GitHub

Create a new repository on GitHub (e.g. `prayaas`), then run:

```bash
# Rename branch to main
git branch -M main

# Add your GitHub remote
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/prayaas.git

# Push the codebase
git push -u origin main
```

---

## Step 2: Deploy Backend & Database on Render

We have provided a production-ready `render.yaml` Blueprint in the root directory.

### Option A: 1-Click Render Blueprint (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository (`prayaas`).
4. Render will read `render.yaml` and automatically configure:
   - **Database**: `prayaas-postgis` (PostgreSQL with PostGIS enabled).
   - **Web Service**: `prayaas-backend` (Docker container built from `backend/Dockerfile`).
   - Automatically injects `DATABASE_URL` linking the service to the database.
   - Automatically sets `CORS_ORIGINS=*`.
5. Click **Apply**.
6. The container automatically:
   - Runs `alembic upgrade head` (enables PostGIS and creates all spatial schemas).
   - Seeds the Chamoli baseline dataset idempotently.
   - Starts the Uvicorn server on `$PORT`.
7. Once deployed, copy your backend URL:
   `https://prayaas-backend.onrender.com`

### Option B: Manual Setup on Render
If configuring manually:
1. **Create PostgreSQL Database**:
   - Name: `prayaas-postgis`
   - Database: `prayaas`
   - User: `prayaas`
   - Plan: Free or Starter
2. **Create Web Service**:
   - Environment: **Docker**
   - Root Directory: `backend` (or build context `backend`, Dockerfile `backend/Dockerfile`)
   - Health Check Path: `/api/health`
   - Environment Variables:
     - `DATABASE_URL`: Paste the Internal Connection String from your database (our backend automatically normalizes `postgres://` to `postgresql+psycopg://`).
     - `APP_ENV`: `production`
     - `APP_DEBUG`: `false`
     - `CORS_ORIGINS`: `*` (or your Vercel URL once known)

---

## Step 3: Deploy Frontend on Vercel

### Option A: Vercel Web Dashboard (Recommended)
1. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New...** → **Project**.
2. Select your `prayaas` repository from GitHub.
3. Configure the Project:
   - **Framework Preset**: `Vite` (automatically detected).
   - **Root Directory**: `./` (leave default).
   - **Build Command**: `npm run build` (or leave default).
   - **Output Directory**: `dist` (handled by `vercel.json`).
4. **Environment Variables**:
   Add the following environment variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://<YOUR_RENDER_BACKEND_URL>` (e.g. `https://prayaas-backend.onrender.com`)
5. Click **Deploy**.
6. Vercel will build and assign your production domain:
   `https://prayaas.vercel.app`

### Option B: Vercel CLI
If deploying via CLI:
```bash
npx vercel
# Follow prompts: Link to existing project or create new.
# Set VITE_API_BASE_URL:
npx vercel env add VITE_API_BASE_URL production
# Enter your Render URL when prompted, then deploy to production:
npx vercel --prod
```

---

## Step 4: Verification Checklist

1. **Backend Health Check**:
   Open in your browser:
   - `https://<YOUR_RENDER_URL>/api/health` → `{"status": "ok", "service": "prayaas-api"}`
   - `https://<YOUR_RENDER_URL>/api/health/database` → `{"status": "ok", "postgis_version": "3.4 ..."}`
   - `https://<YOUR_RENDER_URL>/docs` → Swagger UI with all 20+ endpoints.

2. **Frontend Workstation**:
   Open `https://<YOUR_VERCEL_URL>.vercel.app`:
   - Inspect habitations on the GIS map (Joshimath, Raini, Khar) to verify live multi-hazard risk scores and relocation readiness.
   - Check the bottom drawer for live relocation priorities.
   - Navigate to `/red-zones` to review the statutory area discrepancy audit.
   - Navigate to `/data-sources` to verify real-time data freshness telemetry.
