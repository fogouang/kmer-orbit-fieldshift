from __future__ import annotations

from fastapi import APIRouter

from app.modules.zones.schemas import ClimatOut, SolOut, ZoneOut
from app.modules.zones.service import lire_climat, lire_sol, lire_validation, lister_zones

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=list[ZoneOut], summary="Zones dont les donnees sont pretes")
def get_zones():
    return lister_zones()


@router.get("/{zone}/climat", response_model=ClimatOut, summary="Climat de la zone (donnees NASA)")
def get_climat(zone: str):
    return lire_climat(zone)


@router.get("/{zone}/sol", response_model=SolOut, summary="Profil du sol de la zone (SoilGrids)")
def get_sol(zone: str):
    return lire_sol(zone)


@router.get("/{zone}/validation", summary="Satellite compare a la station meteo au sol (IRAD)")
def get_validation(zone: str):
    return lire_validation(zone)

