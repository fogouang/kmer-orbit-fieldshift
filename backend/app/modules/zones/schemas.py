from __future__ import annotations

from pydantic import BaseModel


class ZoneOut(BaseModel):
    nom: str
    latitude: float | None = None
    longitude: float | None = None


class SaisonClimat(BaseModel):
    saison: str
    mois: list[int]
    pluie_moyenne_mm: float
    pluie_min_mm: float
    pluie_max_mm: float
    temperature_c: float


class PluieMensuelle(BaseModel):
    mois: int
    periode_a_mm: float
    periode_b_mm: float
    ecart_pct: float


class DebutSaison(BaseModel):
    annee: int
    date_imerg: str | None
    jour_imerg: int | None
    jour_power: int | None


class TemperatureAnnuelle(BaseModel):
    annee: int
    temperature_c: float


class ClimatOut(BaseModel):
    zone: str
    sources: dict[str, str]
    annees_reference: list[int]
    saisons: list[SaisonClimat]
    periode_a: str
    periode_b: str
    pluie_mensuelle: list[PluieMensuelle]
    debut_saison: list[DebutSaison]
    temperature_annuelle: list[TemperatureAnnuelle]


class AptitudePh(BaseModel):
    culture: str
    aptitude_ph: str
    detail: str


class SolOut(BaseModel):
    zone: str
    latitude: float | None = None
    longitude: float | None = None
    source: str | None = None
    ph: float
    ph_niveau: str | None = None
    ph_intervalle_90pct: list[float] | None = None
    carbone_organique_g_kg: float | None = None
    carbone_niveau: str | None = None
    azote_g_kg: float | None = None
    argile_pct: float
    limon_pct: float | None = None
    sable_pct: float | None = None
    texture: str | None = None
    cec_cmol_kg: float | None = None
    densite_apparente_kg_dm3: float | None = None
    aptitude_ph_cultures: list[AptitudePh] = []