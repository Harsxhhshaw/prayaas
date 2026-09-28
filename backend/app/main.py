"""PRAYAAS FastAPI application factory.

Supports:
- Swagger/OpenAPI at /docs and /api/docs
- Direct /api/... and versioned /api/v1/... endpoints
- CORS for frontend development
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        version="0.1.0",
        description="PRAYAAS — Intelligent GIS-enabled multi-hazard decision-support API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Mount Endpoints at both /api and /api/v1 ──
    app.include_router(api_router, prefix="/api")
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    @app.get("/api/docs", include_in_schema=False)
    def api_docs():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
