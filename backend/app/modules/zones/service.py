from __future__ import annotations

import json

import pandas as pd
from fastapi import HTTPException, status

from app.config import PROCESSED_DIR
from moteur_rotation import ANNEES_RECENTES, SAISONS, charger_climat

from app.modules.zones.schemas import (
    ClimatOut,
    DebutSaison,
    PluieMensuelle,
    SaisonClimat,
    SolOut,
    TemperatureAnnuelle,
    ZoneOut,
)

# Fichiers indispensables pour qu'une zone soit utilisable par le moteur
FICHIERS_REQUIS = ("{z}_imerg_mensuel.csv", "{z}_mensuel.csv", "{z}_sol.json")


def zone_disponible(zone: str) -> bool:
    return all((PROCESSED_DIR / f.format(z=zone)).exists() for f in FICHIERS_REQUIS)


def verifier_zone(zone: str) -> None:
    if not zone_disponible(zone):
        manquants = [f.format(z=zone) for f in FICHIERS_REQUIS if not (PROCESSED_DIR / f.format(z=zone)).exists()]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone '{zone}' indisponible : fichiers manquants {manquants}. "
                   f"Lance les scripts de preparation des donnees pour cette zone.",
        )


def lister_zones() -> list[ZoneOut]:
    zones = []
    for f in sorted(PROCESSED_DIR.glob("*_sol.json")):
        nom = f.name.removesuffix("_sol.json")
        if zone_disponible(nom):
            sol = json.loads(f.read_text(encoding="utf-8"))
            zones.append(ZoneOut(nom=nom, latitude=sol.get("latitude"), longitude=sol.get("longitude")))
    return zones


def lire_sol(zone: str) -> SolOut:
    verifier_zone(zone)
    data = json.loads((PROCESSED_DIR / f"{zone}_sol.json").read_text(encoding="utf-8"))
    return SolOut(**data)


def lire_climat(zone: str) -> ClimatOut:
    verifier_zone(zone)

    # Saisons : meme calcul que le moteur (10 dernieres annees)
    climat = charger_climat(zone)
    saisons = [
        SaisonClimat(
            saison=s,
            mois=SAISONS[s],
            pluie_moyenne_mm=round(c.pluie_moyenne, 1),
            pluie_min_mm=round(min(c.pluies_annuelles), 1),
            pluie_max_mm=round(max(c.pluies_annuelles), 1),
            temperature_c=round(c.temperature, 2),
        )
        for s, c in climat.items()
    ]

    # Pluie mensuelle IMERG : premiere moitie vs deuxieme moitie de la periode
    imerg = pd.read_csv(PROCESSED_DIR / f"{zone}_imerg_mensuel.csv", parse_dates=["date"]).set_index("date")["pluie_mm"]
    dates = pd.DatetimeIndex(imerg.index)
    debut, fin = dates.year.min(), dates.year.max()
    coupure = debut + (fin - debut + 1) // 2
    a = imerg[dates.year < coupure]
    b = imerg[dates.year >= coupure]
    moy_a = a.groupby(pd.DatetimeIndex(a.index).month).mean()
    moy_b = b.groupby(pd.DatetimeIndex(b.index).month).mean()
    pluie_mensuelle = [
        PluieMensuelle(
            mois=m,
            periode_a_mm=round(float(moy_a[m]), 1),
            periode_b_mm=round(float(moy_b[m]), 1),
            ecart_pct=round(float((moy_b[m] - moy_a[m]) / moy_a[m] * 100), 1) if moy_a[m] else 0.0,
        )
        for m in range(1, 13)
    ]

    # Debut de saison (etape 3), si disponible
    debut_saison = []
    fichier_debut = PROCESSED_DIR / f"{zone}_debut_saison_imerg.csv"
    if fichier_debut.exists():
        df = pd.read_csv(fichier_debut)
        for _, r in df.iterrows():
            debut_saison.append(
                DebutSaison(
                    annee=int(r["annee"]),
                    date_imerg=None if pd.isna(r.get("debut_imerg")) else str(r["debut_imerg"]),
                    jour_imerg=None if pd.isna(r.get("debut_imerg_jour")) else int(r["debut_imerg_jour"]),
                    jour_power=None if pd.isna(r.get("debut_power_jour", float("nan"))) else int(r["debut_power_jour"]),
                )
            )

    # Temperature annuelle (NASA POWER)
    power = pd.read_csv(PROCESSED_DIR / f"{zone}_mensuel.csv", parse_dates=["date"]).set_index("date")["temp_moy_c"]
    temp = power.groupby(pd.DatetimeIndex(power.index).year).mean()
    temperature_annuelle = [
        TemperatureAnnuelle(annee=int(y), temperature_c=round(float(t), 2))
        for y, t in zip(temp.index.tolist(), temp.tolist())
    ]

    return ClimatOut(
        zone=zone,
        sources={
            "pluie": "NASA GPM IMERG V07 (Final Run)",
            "temperature": "NASA POWER",
            "debut_saison": "NASA GPM IMERG V07 journalier",
        },
        annees_reference=list(range(fin - ANNEES_RECENTES + 1, fin + 1)),
        saisons=saisons,
        periode_a=f"{debut}-{coupure - 1}",
        periode_b=f"{coupure}-{fin}",
        pluie_mensuelle=pluie_mensuelle,
        debut_saison=debut_saison,
        temperature_annuelle=temperature_annuelle,
    )


def lire_validation(zone: str) -> dict:
    """Comparaison satellite / station au sol (scripts/station_irad.py), si elle existe."""
    verifier_zone(zone)
    f = PROCESSED_DIR / f"{zone}_station_validation.json"
    if not f.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pas de station au sol pour la zone '{zone}'. Lance scripts/station_irad.py --name {zone}.",
        )
    return json.loads(f.read_text(encoding="utf-8"))
