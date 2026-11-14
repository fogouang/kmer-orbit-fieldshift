"""
Kmer Orbit - Field Shift
Etape 5 : le MOTEUR DE ROTATION.

Il combine les trois entrees de l'enonce avec les priorites de l'agriculteur :
  - climat  : pluie GPM IMERG (10 dernieres annees) + temperature NASA POWER
  - sol     : profil SoilGrids (data/processed/<zone>_sol.json)
  - cultures: data/crops.json (besoins + effet sur le sol + regles de rotation)
  - priorites de l'agriculteur : rendement, eau, sante du sol (notes de 1 a 5)

Fonctionnement :
  1. note chaque culture dans chaque saison (aptitude 0-1) :
       - eau : part des 10 dernieres annees ou la pluie a couvert le besoin
         minimum de la culture, sur tout le cycle ET sur les 2 premiers mois
         apres le semis (risque de debut de saison sec), moins un risque
         d'engorgement pour les cultures sensibles sur sol argileux ;
       - temperature : temperature moyenne de la saison vs optimum de la culture ;
       - sol : pH de la parcelle vs optimum de la culture ;
     - saison deconseillee par l'IRAD : potentiel reduit de 40 % ;
  2. genere toutes les rotations possibles sur 2 ans (4 saisons) en respectant
     les contraintes (saisons possibles, delai de retour, successions interdites
     par l'IRAD, manioc sur 2 saisons) ;
  3. calcule 3 notes sur 100 par rotation : rendement, eau, sante du sol ;
  4. combine ces notes selon les priorites de l'agriculteur ;
  5. propose les 3 meilleures rotations, differentes entre elles, chacune avec
     les raisons de sa note et des conseils pratiques de l'IRAD (outil d'aide a
     la decision : l'agriculteur compare et choisit, le moteur ne decide pas a
     sa place).

Usage :
    uv run scripts/moteur_rotation.py
    uv run scripts/moteur_rotation.py --rendement 5 --eau 2 --sol 3
    uv run scripts/moteur_rotation.py --precedent mais
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from textes_moteur import LANGUES, Textes

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
CROPS_PATH = ROOT / "data" / "crops.json"

# Saisons culturales des hautes terres de l'Ouest (mois inclus)
SAISONS = {
    "saison_1": [3, 4, 5, 6, 7],   # mi-mars a juillet
    "saison_2": [8, 9, 10, 11],    # aout a novembre
}
# 2 ans = 4 saisons
CALENDRIER = [("An 1", "saison_1"), ("An 1", "saison_2"), ("An 2", "saison_1"), ("An 2", "saison_2")]

# Le manioc occupe la parcelle pendant les 2 saisons d'une meme annee (cycle 9 a 18 mois)
SAISONS_OCCUPEES = {"manioc": 2}

ANNEES_RECENTES = 10          # climat de reference : les 10 dernieres annees
SEUIL_ARGILE_ENGORGEMENT = 30 # % d'argile a partir duquel l'engorgement devient un risque
MOIS_DEMARRAGE = 2            # mois apres le semis ou les jeunes plants sont les plus fragiles
FACTEUR_DEMARRAGE = 0.6       # une jeune culture consomme moins d'eau (coefficients culturaux FAO-56)
FACTEUR_SAISON_DECONSEILLEE = 0.6  # saison deconseillee par l'IRAD (pourriture) : potentiel reduit de 40 %
BONUS_SUCCESSION_CONSEILLEE = 5    # succession citee comme bonne par l'IRAD



# --------------------------------------------------------------------------
# 1. Chargement des donnees
# --------------------------------------------------------------------------
@dataclass
class ClimatSaison:
    pluies_annuelles: list[float]   # pluie de la saison, une valeur par annee
    pluies_demarrage: list[float]   # pluie des MOIS_DEMARRAGE premiers mois, une valeur par annee
    pluie_moyenne: float
    temperature: float


def charger_climat(name: str) -> dict[str, ClimatSaison]:
    imerg = pd.read_csv(PROCESSED_DIR / f"{name}_imerg_mensuel.csv", parse_dates=["date"]).set_index("date")["pluie_mm"]
    power = pd.read_csv(PROCESSED_DIR / f"{name}_mensuel.csv", parse_dates=["date"]).set_index("date")["temp_moy_c"]

    # Index de dates explicites (pour Pyrefly : .year et .month existent bien)
    dates_imerg = pd.DatetimeIndex(imerg.index)
    dates_power = pd.DatetimeIndex(power.index)
    derniere = dates_imerg.year.max()
    imerg = imerg[dates_imerg.year > derniere - ANNEES_RECENTES]
    power = power[dates_power.year > derniere - ANNEES_RECENTES]
    dates_imerg = pd.DatetimeIndex(imerg.index)
    dates_power = pd.DatetimeIndex(power.index)

    climat = {}
    for saison, mois in SAISONS.items():
        pluie = imerg[dates_imerg.month.isin(mois)]
        dates_pluie = pd.DatetimeIndex(pluie.index)
        completes = pluie.groupby(dates_pluie.year).count() == len(mois)  # annees completes
        par_annee = pluie.groupby(dates_pluie.year).sum()[completes]
        debut = pluie[dates_pluie.month.isin(mois[:MOIS_DEMARRAGE])]
        dates_debut = pd.DatetimeIndex(debut.index)
        demarrage = debut.groupby(dates_debut.year).sum()[completes]
        temp = power[dates_power.month.isin(mois)].mean()
        climat[saison] = ClimatSaison(
            pluies_annuelles=par_annee.tolist(),
            pluies_demarrage=demarrage.tolist(),
            pluie_moyenne=float(par_annee.mean()),
            temperature=float(temp),
        )
    return climat


def charger_sol(name: str) -> dict:
    return json.loads((PROCESSED_DIR / f"{name}_sol.json").read_text(encoding="utf-8"))


def charger_cultures() -> tuple[dict[str, dict], list[dict]]:
    data = json.loads(CROPS_PATH.read_text(encoding="utf-8"))
    return {c["id"]: c for c in data["cultures"]}, data["regles_rotation"]


def charger_normes(langue: str = "fr") -> dict:
    """Normes generales de l'IRAD (jachere, association, amendement...), dans la langue demandee."""
    return textes(langue).normes(json.loads(CROPS_PATH.read_text(encoding="utf-8")).get("normes_irad", {}))


def textes(langue: str = "fr") -> Textes:
    """Textes du moteur dans la langue demandee (traductions de crops.json incluses)."""
    data = json.loads(CROPS_PATH.read_text(encoding="utf-8"))
    return Textes(langue, data.get("traductions", {}))


# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# 2. Aptitude d'une culture dans une saison (0 a 1)
# --------------------------------------------------------------------------
@dataclass
class Aptitude:
    total: float
    eau_fiabilite: float      # part des annees ou la pluie couvre le besoin minimum (cycle + demarrage)
    engorgement: float        # part des annees a risque d'exces d'eau (0 si non concerne)
    temperature: float
    sol: float
    notes: list[str] = field(default_factory=list)


def score_temperature(t: float, crop: dict) -> float:
    tc = crop["temperature_c"]
    if tc["optimum_min"] <= t <= tc["optimum_max"]:
        return 1.0
    if t < tc["optimum_min"]:
        return max(0.0, (t - tc["absolu_min"]) / (tc["optimum_min"] - tc["absolu_min"]))
    return max(0.0, (tc["absolu_max"] - t) / (tc["absolu_max"] - tc["optimum_max"]))


def score_ph(ph: float, crop: dict) -> tuple[float, str]:
    """pH dans l'optimum IRAD = 1 ; dans la plage toleree = 0,7 ; hors plage = 0,3."""
    p = crop["ph_sol"]
    if p["optimum_min"] <= ph <= p["optimum_max"]:
        return 1.0, "bon"
    lo = p.get("tolere_min", p["optimum_min"] - 0.5)
    hi = p.get("tolere_max", p["optimum_max"] + 0.5)
    if lo <= ph <= hi:
        return 0.7, "limite"
    return 0.3, "défavorable"


def sous_seuil_ph(ph: float, crop: dict) -> bool:
    """Vrai si le pH est sous le seuil critique signale par l'IRAD (nodulation, aluminium)."""
    seuil = crop.get("seuil_ph_critique")
    return bool(seuil and ph < seuil["valeur"])


def aptitude(crop: dict, saisons: list[str], climat: dict[str, ClimatSaison], sol: dict,
             tx: Textes | None = None) -> Aptitude:
    """Aptitude d'une culture semee en saisons[0] et occupant toutes les saisons listees."""
    # Eau : pluie cumulee sur les saisons occupees, annee par annee
    pluies = [sum(v) for v in zip(*(climat[s].pluies_annuelles for s in saisons))]
    besoin_min = crop["besoin_eau_cycle_mm"]["min"]
    besoin_max = crop["besoin_eau_cycle_mm"]["max"]
    fiabilite_cycle = sum(p >= besoin_min for p in pluies) / len(pluies)

    # Demarrage : la pluie des premiers mois doit couvrir la part du besoin correspondante
    duree_mois = crop["cycle_jours"]["min"] / 30
    besoin_demarrage = besoin_min * min(1.0, MOIS_DEMARRAGE / duree_mois) * FACTEUR_DEMARRAGE
    demarrage = climat[saisons[0]].pluies_demarrage
    fiabilite_demarrage = sum(p >= besoin_demarrage for p in demarrage) / len(demarrage)
    fiabilite = 0.6 * fiabilite_cycle + 0.4 * fiabilite_demarrage

    engorgement = 0.0
    if crop["tolerance_exces_eau"] == 1 and sol["argile_pct"] >= SEUIL_ARGILE_ENGORGEMENT:
        engorgement = sum(p > 2 * besoin_max for p in pluies) / len(pluies)
    eau = fiabilite * (1 - 0.5 * engorgement)

    temp_moy = sum(climat[s].temperature for s in saisons) / len(saisons)
    temp = score_temperature(temp_moy, crop)
    ph, ph_niveau = score_ph(sol["ph"], crop)

    tx = tx or Textes()
    notes = []
    if fiabilite_cycle < 1:
        notes.append(tx.msg("pluie_cycle", p=tx.pct(fiabilite_cycle)))
    if fiabilite_demarrage < 1:
        notes.append(tx.msg("debut_sec", p=tx.pct(1 - fiabilite_demarrage),
                            mm=f"{besoin_demarrage:.0f}", n=MOIS_DEMARRAGE))
    if engorgement > 0:
        notes.append(tx.msg("engorgement", p=tx.pct(engorgement)))
    if temp < 1:
        notes.append(tx.msg("temperature", t=tx.dec(temp_moy)))
    if ph_niveau != "bon":
        p = crop["ph_sol"]
        notes.append(tx.msg("sol_ph", niveau=tx.niveau_ph(ph_niveau), ph=tx.ph(sol["ph"]),
                            min=tx.ph(p["optimum_min"]), max=tx.ph(p["optimum_max"])))
    if sous_seuil_ph(sol["ph"], crop):
        notes.append(tx.effet_seuil_ph(crop))

    total = 0.5 * eau + 0.25 * temp + 0.25 * ph

    # Saison deconseillee par l'IRAD (pourriture du haricot en 1re campagne,
    # de la pomme de terre recoltee sous la pluie en 2e campagne)
    deconseillee = tx.saison_deconseillee(crop, saisons[0])
    if deconseillee:
        total *= FACTEUR_SAISON_DECONSEILLEE
        notes.append(tx.msg("saison_deconseillee", raison=deconseillee))

    return Aptitude(total, fiabilite, engorgement, temp, ph, notes)


# --------------------------------------------------------------------------
# 3. Generation des rotations possibles
# --------------------------------------------------------------------------
@dataclass
class Bloc:
    """Une culture placee dans la rotation (peut occuper plusieurs saisons)."""
    crop_id: str
    debut: int                  # indice de saison dans CALENDRIER
    saisons: list[int]


def generer_rotations(cultures: dict[str, dict], precedent: str | None) -> list[list[Bloc]]:
    resultats = []
    n = len(CALENDRIER)

    def autorise(crop_id: str, debut: int, blocs: list[Bloc]) -> bool:
        crop = cultures[crop_id]
        saison = CALENDRIER[debut][1]
        if saison not in crop["saisons_possibles"]:
            return False
        duree = SAISONS_OCCUPEES.get(crop_id, 1)
        if debut + duree > n:
            return False
        delai_saisons = 2 * crop["delai_retour_ans"]
        historique = [(-1, precedent)] if precedent else []
        historique += [(b.debut, b.crop_id) for b in blocs]
        for pos, cid in historique:
            if cid == crop_id and debut - pos < delai_saisons:
                return False
        # Successions interdites par l'IRAD (ex. haricot apres arachide)
        juste_avant = historique[-1][1] if historique else None
        if juste_avant in crop.get("precedents_interdits", []):
            return False
        return True

    def explorer(debut: int, blocs: list[Bloc]):
        if debut >= n:
            resultats.append(list(blocs))
            return
        for crop_id in cultures:
            if autorise(crop_id, debut, blocs):
                duree = SAISONS_OCCUPEES.get(crop_id, 1)
                bloc = Bloc(crop_id, debut, list(range(debut, debut + duree)))
                explorer(debut + duree, blocs + [bloc])

    explorer(0, [])
    return resultats


# --------------------------------------------------------------------------
# 4. Notes d'une rotation
# --------------------------------------------------------------------------
@dataclass
class Evaluation:
    blocs: list[Bloc]
    rendement: float
    eau: float
    sol: float
    total: float = 0.0
    raisons: list[str] = field(default_factory=list)
    conseils: list[str] = field(default_factory=list)


def evaluer(blocs: list[Bloc], cultures, climat, sol, precedent: str | None,
            tx: Textes | None = None) -> Evaluation:
    tx = tx or Textes()
    raisons = []
    aptitudes = []
    fiabilites = []

    for b in blocs:
        crop = cultures[b.crop_id]
        saisons = [CALENDRIER[i][1] for i in b.saisons]
        apt = aptitude(crop, saisons, climat, sol, tx)
        # une culture qui occupe 2 saisons compte pour 2 saisons
        aptitudes += [apt.total] * len(b.saisons)
        bonus_secheresse = 0.05 * (crop["tolerance_secheresse"] - 2)
        fiabilites += [min(1.0, apt.eau_fiabilite * (1 - 0.5 * apt.engorgement) + bonus_secheresse)] * len(b.saisons)
        if apt.notes:
            annee, saison = CALENDRIER[b.debut]
            moment = tx.msg("moment", annee=tx.annee(annee), saison=tx.saison(saison))
            raisons.append(tx.msg("culture_moment", nom=tx.nom(crop), moment=moment, notes=tx.msg("separateur").join(apt.notes)))

    rendement = 100 * sum(aptitudes) / len(aptitudes)
    eau = 100 * sum(fiabilites) / len(fiabilites)

    # Sante du sol : regles de rotation de crops.json
    score_sol = 50.0
    sequence = ([cultures[precedent]] if precedent else []) + [cultures[b.crop_id] for b in blocs]
    for prev, cur in zip(sequence, sequence[1:]):
        a, b_ = tx.nom(prev), tx.nom(cur)
        if cur["id"] in prev.get("suivants_conseilles", []):
            score_sol += BONUS_SUCCESSION_CONSEILLEE
            raisons.append(tx.msg("succession_conseillee", a=a, b=b_))
        if prev["effet_sol"]["fixe_azote"] and cur["effet_sol"]["demande_azote"] == 3:
            gain = 10
            if sous_seuil_ph(sol["ph"], prev) or score_ph(sol["ph"], prev)[1] == "défavorable":
                gain = 5  # la fixation d'azote des legumineuses baisse en sol trop acide
                raisons.append(tx.msg("azote_reduit", a=a, b=b_))
            else:
                raisons.append(tx.msg("azote", a=a, b=b_))
            score_sol += gain
        if prev["famille"] == cur["famille"]:
            score_sol -= 15
            raisons.append(tx.msg("meme_famille", a=a, b=b_))
        if prev["effet_sol"]["demande_azote"] == 3 and cur["effet_sol"]["demande_azote"] == 3:
            score_sol -= 10
            raisons.append(tx.msg("gourmands", a=a, b=b_))

    saison_humide = max(climat, key=lambda s: climat[s].pluie_moyenne)
    for b in blocs:
        crop = cultures[b.crop_id]
        if crop["effet_sol"]["fixe_azote"]:
            score_sol += 5
        score_sol += 3 * (crop["effet_sol"]["couverture_sol"] - 2)
        saison = CALENDRIER[b.debut][1]
        if crop["effet_sol"]["risque_erosion"] >= 3:
            penalite = 10 if saison == saison_humide else 5
            score_sol -= penalite
            raisons.append(tx.msg("erosion", nom=tx.nom(crop), saison=tx.saison(saison))
                           + (tx.msg("erosion_humide") if saison == saison_humide else ""))

    score_sol = max(0.0, min(100.0, score_sol))
    return Evaluation(blocs, rendement, eau, score_sol, raisons=raisons,
                      conseils=conseiller(blocs, cultures, sol, tx))


def conseiller(blocs: list[Bloc], cultures, sol, tx: Textes | None = None) -> list[str]:
    """Conseils pratiques de l'IRAD pour mettre la rotation en oeuvre."""
    tx = tx or Textes()
    ids = [b.crop_id for b in blocs]
    conseils = []
    if sol["ph"] < 5.5:
        conseils.append(tx.msg("conseil_sol_acide", ph=tx.ph(sol["ph"])))
    if "arachide" in ids and sol["ph"] < 5.5:
        conseils.append(tx.msg("conseil_arachide"))
    if "manioc" in ids:
        conseils.append(tx.msg("conseil_manioc"))
    for cid in dict.fromkeys(ids):
        crop = cultures[cid]
        periodes = tx.periodes_critiques(crop)
        if periodes:
            etapes = tx.msg("separateur").join(tx.msg("periode", stade=p["stade"], risque=p["risque"]) for p in periodes)
            conseils.append(tx.msg("conseil_periodes", nom=tx.nom(crop), etapes=etapes))
    return conseils


# --------------------------------------------------------------------------
# 5. Choix des meilleures rotations selon les priorites
# --------------------------------------------------------------------------
def classer(evaluations: list[Evaluation], poids: dict[str, float], nb: int = 3) -> list[Evaluation]:
    somme = sum(poids.values())
    for e in evaluations:
        e.total = (poids["rendement"] * e.rendement + poids["eau"] * e.eau + poids["sol"] * e.sol) / somme
    evaluations.sort(key=lambda e: e.total, reverse=True)

    def composition(e):
        return tuple(sorted(b.crop_id for b in e.blocs))

    retenues = []
    for e in evaluations:
        # chaque proposition doit avoir une composition de cultures differente :
        # de vrais choix, pas le meme plan dans un autre ordre
        if all(composition(e) != composition(r) for r in retenues):
            retenues.append(e)
        if len(retenues) == nb:
            break
    return retenues


def decrire(e: Evaluation, cultures, tx: Textes | None = None) -> str:
    tx = tx or Textes()
    morceaux = []
    for b in e.blocs:
        debut = CALENDRIER[b.debut]
        nom = tx.nom(cultures[b.crop_id])
        if len(b.saisons) > 1:
            fin = CALENDRIER[b.saisons[-1]]
            morceaux.append(f"{nom} ({tx.annee(debut[0])}, {tx.saison(debut[1])} -> {tx.saison(fin[1])})")
        else:
            morceaux.append(f"{nom} ({tx.annee(debut[0])}, {tx.saison(debut[1])})")
    return " -> ".join(morceaux)


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Moteur de rotation Field Shift")
    parser.add_argument("--name", default="dschang")
    parser.add_argument("--rendement", type=int, default=3, choices=range(1, 6),
                        help="Importance du rendement (1 a 5)")
    parser.add_argument("--eau", type=int, default=3, choices=range(1, 6),
                        help="Importance de la securite en eau (1 a 5)")
    parser.add_argument("--sol", type=int, default=3, choices=range(1, 6),
                        help="Importance de la sante du sol (1 a 5)")
    parser.add_argument("--precedent", default=None,
                        help="Culture actuellement sur la parcelle (id de crops.json, ex. mais)")
    parser.add_argument("--nb", type=int, default=3, help="Nombre de rotations proposees")
    parser.add_argument("--langue", default="fr", choices=LANGUES, help="Langue des raisons et conseils")
    args = parser.parse_args()

    cultures, _ = charger_cultures()
    if args.precedent and args.precedent not in cultures:
        raise SystemExit(f"Culture précédente inconnue : {args.precedent}. Choix : {', '.join(cultures)}")
    climat = charger_climat(args.name)
    sol = charger_sol(args.name)

    tx = textes(args.langue)
    rotations = generer_rotations(cultures, args.precedent)
    evaluations = [evaluer(r, cultures, climat, sol, args.precedent, tx) for r in rotations]
    poids = {"rendement": args.rendement, "eau": args.eau, "sol": args.sol}
    meilleures = classer(evaluations, poids, args.nb)

    # Resume console
    print("===== CONTEXTE =====")
    for s, c in climat.items():
        print(f"{tx.saison(s)} : pluie moyenne {c.pluie_moyenne:.0f} mm "
              f"(de {min(c.pluies_annuelles):.0f} à {max(c.pluies_annuelles):.0f} mm selon les années), "
              f"température {c.temperature:.1f} °C")
    print(f"Sol : pH {sol['ph']}, {sol['texture'].lower()}, carbone {sol['carbone_organique_g_kg']} g/kg")
    print(f"Priorités : rendement {args.rendement}/5, eau {args.eau}/5, santé du sol {args.sol}/5"
          + (f" ; culture actuelle : {cultures[args.precedent]['nom']}" if args.precedent else ""))
    print(f"{len(rotations)} rotations possibles évaluées "
          "(délais de retour et successions interdites de l'IRAD respectés).\n")

    sortie = []
    for rang, e in enumerate(meilleures, 1):
        print(f"===== ROTATION {rang} : note {e.total:.0f}/100 =====")
        print(decrire(e, cultures, tx))
        print(f"  Rendement {e.rendement:.0f}/100 | Sécurité en eau {e.eau:.0f}/100 | Santé du sol {e.sol:.0f}/100")
        for r in e.raisons:
            print(f"  - {r}")
        if e.conseils:
            print("  Conseils :")
            for c in e.conseils:
                print(f"    > {c}")
        print()
        sortie.append(
            {
                "rang": rang,
                "note": round(e.total, 1),
                "rendement": round(e.rendement, 1),
                "eau": round(e.eau, 1),
                "sante_sol": round(e.sol, 1),
                "sequence": [
                    {
                        "culture": b.crop_id,
                        "nom": tx.nom(cultures[b.crop_id]),
                        "saisons": [f"{CALENDRIER[i][0]} {CALENDRIER[i][1]}" for i in b.saisons],
                    }
                    for b in e.blocs
                ],
                "raisons": e.raisons,
                "conseils": e.conseils,
            }
        )

    out = PROCESSED_DIR / f"{args.name}_rotations.json"
    out.write_text(json.dumps({"priorites": poids, "precedent": args.precedent, "rotations": sortie,
                               "normes_irad": charger_normes(args.langue)},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats enregistrés : {out}")


if __name__ == "__main__":
    main()