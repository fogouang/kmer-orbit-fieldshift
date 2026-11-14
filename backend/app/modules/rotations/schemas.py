from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class Priorites(BaseModel):
    rendement: int = Field(3, ge=1, le=5, description="Importance du rendement (1 a 5)")
    eau: int = Field(3, ge=1, le=5, description="Importance de la securite en eau (1 a 5)")
    sol: int = Field(3, ge=1, le=5, description="Importance de la sante du sol (1 a 5)")


class SolSaisi(BaseModel):
    """Valeurs d'une analyse de sol de l'agriculteur : remplacent celles de SoilGrids."""
    ph: float | None = Field(None, ge=3.0, le=10.0)
    argile_pct: float | None = Field(None, ge=0, le=100)


class RotationRequest(BaseModel):
    zone: str = "dschang"
    priorites: Priorites = Priorites()
    precedent: str | None = Field(None, description="Culture actuellement sur la parcelle (id, ex. mais)")
    nb: int = Field(3, ge=1, le=5, description="Nombre de rotations proposees")
    sol: SolSaisi | None = None
    langue: Literal["fr", "en"] = Field("fr", description="Langue des raisons, conseils et normes")
    actuelle: list[str | None] | None = Field(
        None,
        min_length=4,
        max_length=4,
        description=(
            "Rotation actuelle de l'agriculteur, saison par saison (An 1 saison 1, An 1 saison 2, "
            "An 2 saison 1, An 2 saison 2) ; null = parcelle au repos. Notee avec les memes criteres."
        ),
    )

class PeriodeCulture(BaseModel):
    annee: str
    saison: str


class EtapeRotation(BaseModel):
    culture: str
    nom: str
    periodes: list[PeriodeCulture]


class RotationOut(BaseModel):
    rang: int
    note: float
    rendement: float
    eau: float
    sante_sol: float
    sequence: list[EtapeRotation]
    raisons: list[str]
    conseils: list[str] = []
    regles_non_respectees: list[str] = []


class SolUtilise(BaseModel):
    ph: float
    argile_pct: float
    source: str


class RotationResponse(BaseModel):
    zone: str
    priorites: Priorites
    precedent: str | None
    sol_utilise: SolUtilise
    nb_rotations_evaluees: int
    rotations: list[RotationOut]
    normes_irad: dict = {}
    actuelle: RotationOut | None = None
