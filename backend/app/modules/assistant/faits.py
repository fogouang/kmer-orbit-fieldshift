"""
Les FAITS donnes a l'assistant : uniquement des donnees de Field Shift.

L'assistant ne recoit rien d'autre que ce texte. Il est construit a chaque question,
a partir des resultats que le serveur recalcule lui-meme (rotations, climat, sol,
validation par la station, fiches cultures et regles de l'IRAD).
"""

from __future__ import annotations

import json

from fastapi import HTTPException

from app.config import CROPS_PATH, PROCESSED_DIR
from app.modules.rotations.schemas import RotationOut, RotationResponse
from app.modules.zones.service import lire_climat, lire_validation

SAISONS = {"saison_1": "1re campagne (mars à juillet)", "saison_2": "2e campagne (août à novembre)"}
ANNEES = {"An 1": "An 1", "An 2": "An 2"}


def _sequence(r: RotationOut) -> str:
    morceaux = []
    for e in r.sequence:
        periodes = ", ".join(f"{ANNEES[p.annee]} {SAISONS[p.saison].split(' (')[0]}" for p in e.periodes)
        morceaux.append(f"{e.nom} ({periodes})")
    return " -> ".join(morceaux)


def _rotation(titre: str, r: RotationOut) -> list[str]:
    lignes = [
        f"### {titre}",
        f"Cultures : {_sequence(r)}",
        f"Note globale : {r.note:.0f}/100 (rendement {r.rendement:.0f}/100, sécurité en eau {r.eau:.0f}/100, "
        f"santé du sol {r.sante_sol:.0f}/100)",
    ]
    if r.regles_non_respectees:
        lignes.append("Règles de l'IRAD NON respectées :")
        lignes += [f"- {x}" for x in r.regles_non_respectees]
    if r.raisons:
        lignes.append("Raisons de la note (calculées par le moteur) :")
        lignes += [f"- {x}" for x in r.raisons]
    if r.conseils:
        lignes.append("Conseils de l'IRAD pour cette rotation :")
        lignes += [f"- {x}" for x in r.conseils]
    return lignes


def _cultures() -> list[str]:
    data = json.loads(CROPS_PATH.read_text(encoding="utf-8"))
    lignes = ["## Fiches des cultures (IRAD Dschang, compléments FAO)"]
    for c in data["cultures"]:
        eau = c["besoin_eau_cycle_mm"]
        ph = c["ph_sol"]
        sol = c["effet_sol"]
        lignes.append(f"### {c['nom']} ({c['famille']}, {c['type']})")
        lignes.append(f"- Cycle : {c['cycle_jours']['min']} à {c['cycle_jours']['max']} jours")
        lignes.append(f"- Saisons possibles : {', '.join(SAISONS[s] for s in c['saisons_possibles'])}")
        for s, d in c.get("dates_semis", {}).items():
            lignes.append(f"- Semis en {SAISONS[s]} : {d}")
        lignes.append(f"- Besoin en eau sur le cycle : {eau['min']} à {eau['max']} mm")
        lignes.append(
            f"- pH du sol : optimum {ph['optimum_min']} à {ph['optimum_max']}, "
            f"toléré {ph.get('tolere_min', '?')} à {ph.get('tolere_max', '?')}"
        )
        if c.get("seuil_ph_critique"):
            lignes.append(f"- Seuil critique : {c['seuil_ph_critique']['effet']}")
        lignes.append(f"- Fixe l'azote de l'air : {'oui (légumineuse)' if sol['fixe_azote'] else 'non'}")
        lignes.append(f"- Demande en azote (1 faible à 3 forte) : {sol['demande_azote']}")
        lignes.append(f"- Délai avant de la remettre sur la même parcelle : {c['delai_retour_ans']} ans")
        if c.get("precedents_interdits"):
            noms = [x["nom"] for x in data["cultures"] if x["id"] in c["precedents_interdits"]]
            lignes.append(f"- Interdit juste après : {', '.join(noms)}")
        if c.get("suivants_conseilles"):
            noms = [x["nom"] for x in data["cultures"] if x["id"] in c["suivants_conseilles"]]
            lignes.append(f"- Bonnes cultures à mettre après : {', '.join(noms)}")
        for s, d in c.get("saisons_deconseillees", {}).items():
            lignes.append(f"- Déconseillé en {SAISONS[s]} : {d}")
        for p in c.get("periodes_critiques", []):
            lignes.append(f"- Période critique, {p['stade']} : {p['risque']}")
        if c.get("sensibilites"):
            lignes.append(f"- Sensibilités : {'; '.join(c['sensibilites'])}")
        if c.get("notes"):
            lignes.append(f"- Note : {c['notes']}")
    return lignes


def _normes(normes: dict) -> list[str]:
    lignes = ["## Règles générales de l'IRAD Dschang"]
    for cle, valeur in normes.items():
        if cle == "exemple_rotation_4_ans":  # pas encore recopie : on ne le donne pas
            continue
        if isinstance(valeur, list):
            lignes += [f"- {cle} : {v}" for v in valeur]
        else:
            lignes.append(f"- {cle} : {valeur}")
    return lignes


def _climat(zone: str) -> list[str]:
    c = lire_climat(zone)
    lignes = [
        "## Climat de la parcelle",
        f"Pluie : {c.sources['pluie']} ; température : {c.sources['temperature']}.",
        f"Années de référence utilisées par le moteur : {c.annees_reference[0]} à {c.annees_reference[-1]}.",
    ]
    for s in c.saisons:
        lignes.append(
            f"- {SAISONS[s.saison]} : pluie moyenne {s.pluie_moyenne_mm:.0f} mm, de {s.pluie_min_mm:.0f} à "
            f"{s.pluie_max_mm:.0f} mm selon les années ; température moyenne {s.temperature_c:.1f} °C"
        )
    dates = [d for d in c.debut_saison if d.date_imerg]
    if dates:
        tot = min(dates, key=lambda d: d.jour_imerg or 999)
        tard = max(dates, key=lambda d: d.jour_imerg or 0)
        lignes.append(
            f"Début de la saison des pluies (GPM IMERG, {dates[0].annee} à {dates[-1].annee}) : "
            f"le plus tôt le {tot.date_imerg}, le plus tard le {tard.date_imerg}. "
            "La date change d'une année à l'autre."
        )
    return lignes


def _validation(zone: str) -> list[str]:
    try:
        v = lire_validation(zone)
    except HTTPException:
        return []
    im, po = v["pluie_mensuelle"]["imerg"], v["pluie_mensuelle"]["power"]
    an = v["pluie_annuelle"]
    lignes = [
        "## Vérification des données satellite avec la station météo de l'IRAD Dschang",
        f"Période comparée : {v['periode_pluie']}, {im['nb_mois']} mois.",
        f"- GPM IMERG (utilisé par l'outil pour la pluie) : corrélation mensuelle {im['correlation']}, "
        f"écart moyen {im['biais_pct']} %, erreur moyenne {im['erreur_absolue_moyenne']} mm par mois.",
        f"- NASA POWER (pas utilisé pour la pluie) : corrélation {po['correlation']}, "
        f"surestime la pluie de {po['biais_pct']} %, erreur moyenne {po['erreur_absolue_moyenne']} mm par mois.",
        f"- Pluie annuelle moyenne : station {an['station_moyenne_mm']:.0f} mm, IMERG {an['imerg_moyenne_mm']:.0f} mm, "
        f"POWER {an['power_moyenne_mm']:.0f} mm.",
    ]
    for s, d in v.get("pluie_par_saison", {}).items():
        nom = SAISONS.get(s, s)
        lignes.append(
            f"- {nom} : station {d['station_moyenne_mm']:.0f} mm, IMERG {d['imerg_moyenne_mm']:.0f} mm "
            f"(écart {d['ecart_pct']} %)"
        )
    t = v.get("temperature_mensuelle_power")
    if t:
        lignes.append(
            f"- Température NASA POWER comparée à la station : écart moyen {t['biais_moyen']} °C, "
            f"corrélation {t['correlation']} (peu fiable, à confirmer localement)."
        )
    return lignes


def _sol(zone: str, res: RotationResponse) -> list[str]:
    lignes = ["## Sol de la parcelle"]
    f = PROCESSED_DIR / f"{zone}_sol.json"
    estime = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    lignes.append(f"Sol utilisé pour les notes : pH {res.sol_utilise.ph}, argile {res.sol_utilise.argile_pct:.0f} %, "
                  f"source : {res.sol_utilise.source}.")
    if estime:
        lignes.append(
            f"Estimation SoilGrids (modèle à 250 m, pas une analyse de laboratoire) : pH {estime.get('ph')}, "
            f"carbone organique {estime.get('carbone_organique_g_kg')} g/kg, texture {estime.get('texture')}."
        )
        if estime.get("ph_intervalle_90pct"):
            bas, haut = estime["ph_intervalle_90pct"]
            lignes.append(
                f"Incertitude SoilGrids sur le pH : le vrai pH est probablement entre {bas} et {haut}. "
                "Seule une analyse de sol de la parcelle permet de le confirmer."
            )
    return lignes


def construire_faits(res: RotationResponse, normes: dict) -> str:
    """Texte complet des faits, a placer dans le message systeme de l'assistant."""
    p = res.priorites
    lignes = [
        "# FAITS FIELD SHIFT",
        f"Zone : {res.zone} (zone pilote, hautes terres de l'Ouest Cameroun).",
        f"Priorités choisies par l'agriculteur (1 peu important à 5 essentiel) : rendement {p.rendement}, "
        f"sécurité en eau {p.eau}, santé du sol {p.sol}.",
        f"Culture actuellement en place : {res.precedent or 'aucune (parcelle libre)'}.",
        f"Le moteur a évalué {res.nb_rotations_evaluees} rotations possibles sur 2 ans et affiche les meilleures.",
        "Les notes mesurent l'adaptation des cultures au climat et au sol (0 à 100), PAS un rendement en tonnes "
        "ni un revenu.",
        "",
        "## Rotations affichées à l'écran",
    ]
    if res.actuelle:
        lignes += _rotation("Rotation habituelle de l'agriculteur", res.actuelle)
        for r in res.rotations:
            ecart = round(r.note) - round(res.actuelle.note)
            signe = f"+{ecart}" if ecart > 0 else str(ecart)
            lignes.append(f"Écart de l'option {r.rang} avec la rotation habituelle : {signe} points.")
    for r in res.rotations:
        lignes += _rotation(f"Option {r.rang}" + (" (meilleur choix)" if r.rang == 1 else ""), r)
    lignes.append("")
    lignes += _sol(res.zone, res)
    lignes.append("")
    lignes += _climat(res.zone)
    lignes.append("")
    lignes += _validation(res.zone)
    lignes.append("")
    lignes += _normes(normes)
    lignes.append("")
    lignes += _cultures()
    return "\n".join(lignes)