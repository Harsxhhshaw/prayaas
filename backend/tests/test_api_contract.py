"""API Contract Test — Verifies that all endpoints defined in frontend apiRoutes.ts
actually exist and match route definitions in the backend FastAPI application.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest
from app.main import app


def get_frontend_api_routes() -> list[str]:
    """Parses route string constants from src/lib/apiRoutes.ts."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    routes_file = repo_root / "src" / "lib" / "apiRoutes.ts"
    assert routes_file.exists(), f"Route definition file not found at {routes_file}"

    content = routes_file.read_text(encoding="utf-8")
    matches = re.findall(r":\s*['\"](/api/[^'\"]+)['\"]", content)
    assert len(matches) >= 20, f"Expected at least 20 API routes, found {len(matches)}"
    return sorted(list(set(matches)))


def test_frontend_routes_exist_in_backend():
    """Validates that every API route defined in frontend apiRoutes.ts exists in FastAPI app routes."""
    frontend_routes = get_frontend_api_routes()
    backend_routes = set()

    for route in app.routes:
        if hasattr(route, "path"):
            backend_routes.add(route.path)

    missing_routes = []
    for fr in frontend_routes:
        if fr not in backend_routes:
            missing_routes.append(fr)

    assert not missing_routes, f"Frontend routes missing in FastAPI backend: {missing_routes}"


def test_openapi_schema_matches_contract():
    """Validates that core analysis, optimization, and governance endpoints exist in OpenAPI schema."""
    schema = app.openapi()
    paths = schema.get("paths", {})

    critical_paths = [
        "/api/health",
        "/api/health/database",
        "/api/habitations",
        "/api/hazard-zones",
        "/api/optimization/run",
        "/api/digital-twin/simulate",
        "/api/governance/demo-snapshot/raini",
        "/api/governance/habitations/{habitation_id}/dossier",
        "/api/governance/data-honesty-audit",
    ]

    for cp in critical_paths:
        assert cp in paths, f"Critical endpoint {cp} missing from OpenAPI schema paths"
