# PRAYAAS Production Deployment Guide & Live Services Reference

This document tracks the live production deployment of the **PRAYAAS Geospatial Intelligence Platform** on **Render** (FastAPI + PostGIS) and **Vercel** (Vite + React GIS Workstation).

---

## Live Deployments (Verified & Active)

| Component | Platform | Live URL / Endpoint | Status |
| :--- | :--- | :--- | :--- |
| **GitHub Repository** | GitHub | [https://github.com/Harsxhhshaw/prayaas](https://github.com/Harsxhhshaw/prayaas) | `main` branch synced |
| **Backend API (Base)** | Render | [https://prayaas-backend-y1e6.onrender.com](https://prayaas-backend-y1e6.onrender.com) | **200 OK** |
| **API Health Check** | Render | [https://prayaas-backend-y1e6.onrender.com/api/health](https://prayaas-backend-y1e6.onrender.com/api/health) | `{"status":"ok","service":"prayaas-api"}` |
| **Database & PostGIS** | Render | [https://prayaas-backend-y1e6.onrender.com/api/health/database](https://prayaas-backend-y1e6.onrender.com/api/health/database) | `PostGIS 3.6 USE_GEOS=1 USE_PROJ=1` |
| **Interactive Docs** | Render | [https://prayaas-backend-y1e6.onrender.com/docs](https://prayaas-backend-y1e6.onrender.com/docs) | Swagger UI |
| **Frontend Workstation** | Vercel | [https://prayaas-7fxgsq80i-harsxhhshaws-projects.vercel.app](https://prayaas-7fxgsq80i-harsxhhshaws-projects.vercel.app) | **200 OK** |
| **Production Alias** | Vercel | [https://prayaas-five.vercel.app](https://prayaas-five.vercel.app) | Aliased |
| **Vercel Dashboard** | Vercel | [https://vercel.com/harsxhhshaws-projects/prayaas](https://vercel.com/harsxhhshaws-projects/prayaas) | Project Configured |

---

## Architecture Overview

```
┌─────────────────────────────────────────┐           ┌──────────────────────────────────────────────┐
│             VERCEL FRONTEND             │           │                RENDER BACKEND                │
│  Vite + React 19 + TypeScript + Leaflet │           │  FastAPI + SQLAlchemy 2.0 + GeoAlchemy2      │
│  URL: https://prayaas-five.vercel.app   │──(HTTPS)─▶│  URL: https://prayaas-backend-y1e6.onrender.com│
└─────────────────────────────────────────┘           └──────────────────────┬───────────────────────┘
                                                                             │ (PostgreSQL)
                                                      ┌──────────────────────▼───────────────────────┐
                                                      │           RENDER POSTGIS DATABASE            │
                                                      │  PostgreSQL 16 + PostGIS 3.6                 │
                                                      │  Tables: habitations, hazard_zones,          │
                                                      │  candidate_sites, relocation_evaluations...  │
                                                      └──────────────────────────────────────────────┘
```

---

## Deployed Features & Live Verification

### 1. Backend & PostGIS (Render)
- **Container**: Docker image based on `python:3.12-slim` with system GEOS/Proj dependencies.
- **Auto-Migration**: Startup runs `alembic upgrade head`, ensuring PostGIS extension is initialized and all tables/indexes are created.
- **Auto-Seeding**: Runs `python -m app.seeds.seed_chamoli` idempotently.
- **CORS Handling**: Supports both JSON arrays and raw string origins (including wildcards and Vercel domains).

### 2. Frontend GIS Workstation (Vercel)
- **Framework**: Vite + React 19 + TypeScript.
- **Environment Variables**: `VITE_API_BASE_URL` should be configured in the **Vercel Dashboard** under Project Settings → Environment Variables (set to `https://prayaas-backend-y1e6.onrender.com`). Do not commit `.env.production` to source control.
- **Client Routing**: Configured with SPA rewrites to ensure direct route visits (`/red-zones`, `/data-sources`, `/relocation-priority`) load smoothly without 404s.

---

## Operational Notes & Infrastructure Warnings

> [!WARNING]
> **Render Free Tier Limitations & Expiry**:
> 1. **PostgreSQL Expiry**: Render free PostgreSQL instances automatically expire **30 days** after creation, followed by a **14-day grace period** before deletion.
> 2. **Cold Starts**: Render free tier web services spin down / sleep after **15 minutes of inactivity**. Waking a sleeping backend may take 50–90 seconds on first request.
> 
> **Migration & Fallback Options**:
> - **Render Paid Tier / Supabase / Neon / AWS RDS**: Upgrade or attach an external managed PostgreSQL + PostGIS instance by updating the `DATABASE_URL` environment variable.
> - **Offline Demo Snapshot**: PRAYAAS includes a standalone, frozen local demo snapshot (`src/data/raini-snapshot.json`) exported via `/api/governance/demo-snapshot/raini` that automatically services the entire decision workflow (Raini assessment, candidate discovery, relocation plans, robustness evaluation, and dossier) when the backend is sleeping or offline.

---

## Verification Endpoints

1. **System Health**:
   - `GET /api/health` → `{"status": "ok", "service": "prayaas-api"}`
   - `GET /api/health/database` → `{"status": "ok", "database": "postgresql+postgis", "postgis_version": "3.6 ..."}`

2. **Geospatial & Risk Intelligence**:
   - `GET /api/habitations` → Returns Chamoli settlements with live multi-hazard risk scores, vulnerability vectors, and relocation urgency.
   - `GET /api/hazard-zones/geojson` → GeoJSON feature collections for landslide, flood, and subsidence polygons.
   - `GET /api/candidate-sites` → Preliminary candidate relocation sites evaluated for carrying capacity and slope suitability.
   - `GET /api/relocation-priorities` → Multi-criteria relocation prioritization queue.
