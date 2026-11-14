from __future__ import annotations

import app.config  # noqa: F401  (ajoute scripts/ au chemin pour importer le moteur)
from moteur_rotation import charger_cultures

from app.modules.cultures.schemas import CultureOut


def lister_cultures() -> list[CultureOut]:
    cultures, _ = charger_cultures()
    return [
        CultureOut(
            id=c["id"],
            nom=c["nom"],
            nom_scientifique=c["nom_scientifique"],
            famille=c["famille"],
            type=c["type"],
            cycle_jours=c["cycle_jours"],
            saisons_possibles=c["saisons_possibles"],
            besoin_eau_cycle_mm=c["besoin_eau_cycle_mm"],
            ph_optimum={"min": c["ph_sol"]["optimum_min"], "max": c["ph_sol"]["optimum_max"]},
            temperature_optimum={"min": c["temperature_c"]["optimum_min"], "max": c["temperature_c"]["optimum_max"]},
            tolerance_secheresse=c["tolerance_secheresse"],
            tolerance_exces_eau=c["tolerance_exces_eau"],
            effet_sol=c["effet_sol"],
            sensibilites=c["sensibilites"],
            delai_retour_ans=c["delai_retour_ans"],
            notes=c["notes"],
        )
        for c in cultures.values()
    ]