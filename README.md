# PRAYAAS (SIH26191)
### Intelligent GIS-Enabled Decision-Support Platform for Multi-Hazard Disaster Intelligence

PRAYAAS dynamically identifies multi-hazard Red Zones unsuitable for permanent habitation, assesses the suitability and carrying capacity of safer alternative relocation sites, prioritizes vulnerable habitations, and empowers State Disaster Management Authorities (SDMAs) with evidence-based planning.

---

## Architecture Overview

- **Frontend**: Vite + React 19 + TypeScript 6 + Tailwind CSS v4 + Leaflet GIS workstation interface (Palantir/Sentinel Hub-inspired analyst UI).
- **Backend**: Python 3.12+ + FastAPI + Pydantic v2 + SQLAlchemy 2.x + GeoAlchemy2 + psycopg (v3) + Alembic.
- **Spatial Database**: PostgreSQL 16 + PostGIS 3.4 (EPSG:4326 geometry, RFC 7946 GeoJSON, spherical/geodesic distance and area calculations).

---

## Quick Start with Docker (Recommended)

To run the PostgreSQL + PostGIS database and FastAPI backend container stack:

```bash
# 1. Start PostGIS and Backend via Docker Compose
docker compose up -d --build

# 2. View backend logs
docker compose logs -f backend

# 3. Check health
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/database

# 4. Open interactive Swagger API documentation
# http://localhost:8000/docs
```

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"

# Configure environment variables
# Copy .env.example to .env and adjust your PostgreSQL credentials
cp .env.example .env

# Run database migrations
alembic upgrade head

# Run deterministic demo seed for Chamoli
python -m app.seeds.seed_chamoli

# Launch FastAPI development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI Swagger UI is available at:
- **`http://localhost:8000/docs`**
- **`http://localhost:8000/api/docs`**

### 2. Frontend Setup

```bash
# From repository root
npm install

# Start Vite development server
npm run dev

# Run TypeScript typecheck and production build
npm run build
```

Frontend workstation will be live at `http://localhost:5173`.
The top command bar displays real-time connectivity status:
- `API LIVE` (green indicator when backend is online at `http://localhost:8000`)
- `STANDALONE` (amber indicator fallback to embedded prototype data if offline)

---

## Running Backend Tests

All backend tests (spatial calculations, GeoJSON ordering, Pydantic schemas, API routers, and seed integrity) run via `pytest`:

```bash
cd backend
python -m pytest -v
```

---

## Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/health/database` | Database connection & PostGIS version |
| `GET` | `/api/states` | List administrative states |
| `GET` | `/api/districts` | List districts (filterable by `?state=...`) |
| `GET` | `/api/habitations` | List habitations (supports `?district=`, `?riskCategory=`, `?urgency=`, `?bbox=`) |
| `GET` | `/api/habitations/{id}` | Detailed habitation record |
| `GET` | `/api/habitations/geojson` | RFC 7946 GeoJSON FeatureCollection (`[lng, lat]`) |
| `GET` | `/api/hazard-zones` | Statutory Red Zones (alias `/api/red-zones`) |
| `GET` | `/api/hazard-zones/geojson` | GeoJSON polygon boundaries for hazard zones |
| `GET` | `/api/candidate-sites` | Alternative relocation sites with suitability scores |
| `GET` | `/api/candidate-sites/geojson` | GeoJSON polygon boundaries and centroids |
| `GET` | `/api/infrastructure` | Critical infrastructure assets (hospitals, bridges, etc.) |
| `GET` | `/api/infrastructure/geojson` | GeoJSON point features for infrastructure |
| `GET` | `/api/data-sources` | External telemetry feeds (ISRO, IMD, USGS) |
| `GET` | `/api/disaster-events` | Historical disaster catalog (2021 Chamoli Flood, 2023 Joshimath) |
| `GET` | `/api/metrics/summary` | Real-time aggregate KPIs for Command Centre strip |
