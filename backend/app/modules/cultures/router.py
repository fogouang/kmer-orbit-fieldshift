from __future__ import annotations

from fastapi import APIRouter

from app.modules.cultures.schemas import CultureOut
from app.modules.cultures.service import lister_cultures

router = APIRouter(prefix="/cultures", tags=["Cultures"])


@router.get("", response_model=list[CultureOut], summary="Liste des cultures et de leurs besoins")
def get_cultures():
    return lister_cultures()