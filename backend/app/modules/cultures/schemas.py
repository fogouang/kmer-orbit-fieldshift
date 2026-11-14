from __future__ import annotations

from pydantic import BaseModel


class Intervalle(BaseModel):
    min: float
    max: float


class EffetSol(BaseModel):
    fixe_azote: bool
    demande_azote: int
    couverture_sol: int
    enracinement: str
    risque_erosion: int


class CultureOut(BaseModel):
    id: str
    nom: str
    nom_scientifique: str
    famille: str
    type: str
    cycle_jours: Intervalle
    saisons_possibles: list[str]
    besoin_eau_cycle_mm: Intervalle
    ph_optimum: Intervalle
    temperature_optimum: Intervalle
    tolerance_secheresse: int
    tolerance_exces_eau: int
    effet_sol: EffetSol
    sensibilites: list[str]
    delai_retour_ans: int
    notes: str