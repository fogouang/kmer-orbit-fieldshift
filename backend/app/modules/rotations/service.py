from __future__ import annotations

from fastapi import HTTPException

import app.config  # noqa: F401  (ajoute scripts/ au chemin pour importer le moteur)
from moteur_rotation import (
    CALENDRIER,
    charger_climat,
    charger_cultures,
    charger_normes,
    charger_sol,
    classer,
    evaluer,
    generer_rotations,
    textes,
)

from app.modules.rotations.schemas import (
    EtapeRotation,
    PeriodeCulture,
    RotationOut,
    RotationRequest,
    RotationResponse,
    SolUtilise,
)
from app.modules.zones.service import verifier_zone

# Origine des valeurs de sol utilisees, dans la langue de la requete
SOURCES_SOL = {
    "fr": {"soilgrids": "ISRIC SoilGrids (estimation 250 m)", "analyse": "analyse de sol saisie par l'agriculteur"},
    "en": {"soilgrids": "ISRIC SoilGrids (250 m estimate)", "analyse": "soil test entered by the farmer"},
}


def proposer_rotations(req: RotationRequest) -> RotationResponse:
    verifier_zone(req.zone)
    cultures, _ = charger_cultures()

    if req.precedent and req.precedent not in cultures:
        raise HTTPException(
            status_code=422,
            detail=f"Culture precedente inconnue : '{req.precedent}'. Choix possibles : {list(cultures)}",
        )

    climat = charger_climat(req.zone)
    sol = charger_sol(req.zone)

    # Analyse de sol de l'agriculteur : elle remplace les estimations SoilGrids
    source_sol = SOURCES_SOL[req.langue]["soilgrids"]
    if req.sol and (req.sol.ph is not None or req.sol.argile_pct is not None):
        if req.sol.ph is not None:
            sol["ph"] = req.sol.ph
        if req.sol.argile_pct is not None:
            sol["argile_pct"] = req.sol.argile_pct
        source_sol = SOURCES_SOL[req.langue]["analyse"]

    # Textes du moteur (raisons, conseils, noms des cultures) dans la langue demandee
    tx = textes(req.langue)
    rotations = generer_rotations(cultures, req.precedent)
    evaluations = [evaluer(r, cultures, climat, sol, req.precedent, tx) for r in rotations]
    poids = req.priorites.model_dump()
    meilleures = classer(evaluations, poids, req.nb)

    return RotationResponse(
        zone=req.zone,
        priorites=req.priorites,
        precedent=req.precedent,
        sol_utilise=SolUtilise(ph=sol["ph"], argile_pct=sol["argile_pct"], source=source_sol),
        nb_rotations_evaluees=len(rotations),
        rotations=[
            RotationOut(
                rang=rang,
                note=round(e.total, 1),
                rendement=round(e.rendement, 1),
                eau=round(e.eau, 1),
                sante_sol=round(e.sol, 1),
                sequence=[
                    EtapeRotation(
                        culture=b.crop_id,
                        nom=tx.nom(cultures[b.crop_id]),
                        periodes=[PeriodeCulture(annee=CALENDRIER[i][0], saison=CALENDRIER[i][1]) for i in b.saisons],
                    )
                    for b in e.blocs
                ],
                raisons=e.raisons,
                conseils=e.conseils,
            )
            for rang, e in enumerate(meilleures, 1)
        ],
        normes_irad=charger_normes(req.langue),
    )