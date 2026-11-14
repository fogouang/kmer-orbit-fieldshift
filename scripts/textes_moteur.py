"""
Kmer Orbit - Field Shift
Textes du moteur de rotation en francais et en anglais.

Le moteur ne contient plus de phrases en dur : il demande ses textes a Textes(langue).
Les textes des cultures (nom, saison deconseillee, periodes critiques...) et les normes
de l'IRAD viennent de data/crops.json ; leur traduction anglaise est dans le bloc
"traductions.en" du meme fichier.
"""

from __future__ import annotations

LANGUES = ("fr", "en")

# Libelles courts (saisons, annees, niveaux de pH), separes des phrases pour un typage simple
LIBELLES: dict[str, dict[str, dict[str, str]]] = {
    "fr": {
        "saison": {"saison_1": "1re campagne", "saison_2": "2e campagne"},
        "annee": {"An 1": "An 1", "An 2": "An 2"},
        "niveau_ph": {"limite": "limite", "défavorable": "défavorable"},
    },
    "en": {
        "saison": {"saison_1": "1st season", "saison_2": "2nd season"},
        "annee": {"An 1": "Year 1", "An 2": "Year 2"},
        "niveau_ph": {"limite": "borderline", "défavorable": "unfavourable"},
    },
}

# Phrases du moteur ({...} = valeurs inserees)
MESSAGES: dict[str, dict[str, str]] = {
    "fr": {
        "pluie_cycle": "pluie suffisante sur le cycle {p} des années seulement",
        "debut_sec": "début de cycle trop sec {p} des années (besoin d'environ {mm} mm les {n} premiers mois)",
        "engorgement": "risque d'excès d'eau sur sol argileux {p} des années",
        "temperature": "température ({t} °C) hors optimum",
        "sol_ph": "sol {niveau} pour cette culture (pH {ph}, optimum IRAD {min}-{max})",
        "saison_deconseillee": "saison déconseillée par l'IRAD : {raison}",
        "culture_moment": "{nom} ({moment}) : {notes}",
        "moment": "{annee}, {saison}",
        "succession_conseillee": "{a} puis {b} : succession conseillée par l'IRAD",
        "azote_reduit": "{a} avant {b} : apport d'azote, mais réduit par l'acidité du sol",
        "azote": "{a} avant {b} : la légumineuse enrichit le sol en azote",
        "meme_famille": "{a} puis {b} : même famille, risque de maladies",
        "gourmands": "{a} puis {b} : deux cultures gourmandes à la suite, sol épuisé",
        "erosion": "{nom} en {saison} : sol peu couvert, risque d'érosion",
        "erosion_humide": " (saison la plus pluvieuse)",
        "conseil_sol_acide": "Sol acide (pH {ph}) : apporter 5 à 10 t/ha de compost ou de fumier "
                             "et de la cendre pour remonter le pH vers 5,5-6,5 (IRAD).",
        "conseil_arachide": "Arachide : apporter de la cendre, elle a besoin de calcium en sol acide (IRAD).",
        "conseil_manioc": "Le manioc épuise la potasse : après lui, une légumineuse puis le maïs, "
                          "et un apport de cendre ou de fumier (IRAD).",
        "conseil_periodes": "{nom}, périodes à surveiller : {etapes}.",
        "periode": "{stade} : {risque}",
        "separateur": " ; ",
        "succession_interdite": "{a} puis {b} : succession interdite par l'IRAD",
        "retour_trop_tot": "{nom} revient après {n} campagne(s) seulement : l'IRAD conseille d'attendre {ans} ans",
        "hors_saison": "{nom} semé en {saison} : hors de ses saisons habituelles",
        "repos": "Parcelle au repos ({moment}) : le sol se reconstitue, mais rien n'est récolté",
    },
    "en": {
        "pluie_cycle": "enough rain over the cycle in only {p} of years",
        "debut_sec": "start of the cycle too dry in {p} of years (needs about {mm} mm in the first {n} months)",
        "engorgement": "risk of waterlogging on clay soil in {p} of years",
        "temperature": "temperature ({t} °C) outside the optimum",
        "sol_ph": "{niveau} soil for this crop (pH {ph}, IRAD optimum {min}-{max})",
        "saison_deconseillee": "season not recommended by IRAD: {raison}",
        "culture_moment": "{nom} ({moment}): {notes}",
        "moment": "{annee}, {saison}",
        "succession_conseillee": "{a} then {b}: sequence recommended by IRAD",
        "azote_reduit": "{a} before {b}: adds nitrogen, but less because of soil acidity",
        "azote": "{a} before {b}: the legume enriches the soil with nitrogen",
        "meme_famille": "{a} then {b}: same family, disease risk",
        "gourmands": "{a} then {b}: two heavy feeders in a row, depleted soil",
        "erosion": "{nom} in the {saison}: little ground cover, erosion risk",
        "erosion_humide": " (wettest season)",
        "conseil_sol_acide": "Acidic soil (pH {ph}): apply 5 to 10 t/ha of compost or manure "
                             "and wood ash to raise the pH towards 5.5-6.5 (IRAD).",
        "conseil_arachide": "Groundnut: apply wood ash, it needs calcium on acidic soil (IRAD).",
        "conseil_manioc": "Cassava depletes potassium: follow it with a legume, then maize, "
                          "and apply ash or manure (IRAD).",
        "conseil_periodes": "{nom}, critical periods: {etapes}.",
        "periode": "{stade}: {risque}",
        "separateur": "; ",
        "succession_interdite": "{a} then {b}: sequence forbidden by IRAD",
        "retour_trop_tot": "{nom} comes back after only {n} season(s): IRAD advises waiting {ans} years",
        "hors_saison": "{nom} sown in the {saison}: outside its usual seasons",
        "repos": "Plot left to rest ({moment}): the soil recovers, but nothing is harvested",
    },
}


class Textes:
    """Textes du moteur dans une langue donnee (fr par defaut)."""

    def __init__(self, langue: str = "fr", traductions: dict | None = None):
        self.langue = langue if langue in LANGUES else "fr"
        self.m = MESSAGES[self.langue]
        # traductions des textes de crops.json pour cette langue (vide en francais)
        self.tr = (traductions or {}).get(self.langue, {}) if self.langue != "fr" else {}
        self.lib = LIBELLES[self.langue]

    # ---- formats de nombres ----
    def dec(self, x: float, chiffres: int = 1) -> str:
        texte = f"{x:.{chiffres}f}"
        return texte.replace(".", ",") if self.langue == "fr" else texte

    def ph(self, x: float) -> str:
        texte = f"{x:g}"
        return texte.replace(".", ",") if self.langue == "fr" else texte

    def pct(self, x: float) -> str:
        return f"{x:.0%}".replace("%", " %") if self.langue == "fr" else f"{x:.0%}"

    # ---- phrases ----
    def msg(self, cle: str, **valeurs) -> str:
        return self.m[cle].format(**valeurs)

    def saison(self, s: str) -> str:
        return self.lib["saison"][s]

    def annee(self, a: str) -> str:
        return self.lib["annee"][a]

    def niveau_ph(self, niveau: str) -> str:
        return self.lib["niveau_ph"].get(niveau, niveau)

    # ---- textes venant de crops.json ----
    def _culture(self, crop: dict) -> dict:
        return self.tr.get("cultures", {}).get(crop["id"], {})

    def nom(self, crop: dict) -> str:
        return self._culture(crop).get("nom", crop["nom"])

    def saison_deconseillee(self, crop: dict, saison: str) -> str | None:
        fr = crop.get("saisons_deconseillees", {}).get(saison)
        if not fr:
            return None
        return self._culture(crop).get("saisons_deconseillees", {}).get(saison, fr)

    def effet_seuil_ph(self, crop: dict) -> str:
        return self._culture(crop).get("seuil_ph_critique", crop["seuil_ph_critique"]["effet"])

    def periodes_critiques(self, crop: dict) -> list[dict]:
        return self._culture(crop).get("periodes_critiques", crop.get("periodes_critiques", []))

    def normes(self, normes_fr: dict) -> dict:
        return {**normes_fr, **self.tr.get("normes_irad", {})}