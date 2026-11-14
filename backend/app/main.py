"""
Kmer Orbit - Field Shift : API.

Lancement (depuis la racine du projet) :
    uv run uvicorn app.main:app --reload --app-dir backend

Documentation interactive : http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_PREFIX, CORS_ORIGIN_REGEX
from app.modules.cultures.router import router as cultures_router
from app.modules.rotations.router import router as rotations_router
from app.modules.zones.router import router as zones_router

app = FastAPI(
    title="Field Shift API",
    description=(
        "Outil d'aide a la decision pour les rotations de cultures, a partir des "
        "observations de la Terre de la NASA. Equipe Kmer Orbit, NASA Space Apps 2026."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{API_PREFIX}/health", tags=["Sante"])
def health():
    return {"status": "ok"}


app.include_router(cultures_router, prefix=API_PREFIX)
app.include_router(zones_router, prefix=API_PREFIX)
app.include_router(rotations_router, prefix=API_PREFIX)