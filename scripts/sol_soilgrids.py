"""
Kmer Orbit - Field Shift
Etape 4 : le SOL de la parcelle, avec ISRIC SoilGrids (resolution 250 m).

C'est la deuxieme entree exigee par l'enonce ("local soil information").

Ce script :
  1. interroge l'API SoilGrids pour un point GPS (une seule requete, sans compte) ;
  2. recupere 8 proprietes du sol sur 3 profondeurs (0-5, 5-15, 15-30 cm) ;
  3. calcule la moyenne sur 0-30 cm (la zone ou travaillent les racines
     de la plupart des cultures) ;
  4. determine la texture du sol (triangle USDA) ;
  5. compare le pH avec les besoins de chaque culture de data/crops.json.

Usage :
    uv run scripts/sol_soilgrids.py
    uv run scripts/sol_soilgrids.py --lat 5.44 --lon 10.05 --name dschang
    uv run scripts/sol_soilgrids.py --offline   # relit la reponse deja telechargee

Les valeurs SoilGrids sont des estimations par modele a 250 m, pas une
analyse de sol de la parcelle : elles donnent un bon ordre de grandeur,
a confirmer par une analyse en laboratoire si possible.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import pandas as pd
import requests

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CROPS_PATH = ROOT / "data" / "crops.json"

# propriete SoilGrids -> (nom lisible, unite apres conversion)
PROPRIETES = {
    "phh2o": ("pH (eau)", ""),
    "soc": ("Carbone organique", "g/kg"),
    "nitrogen": ("Azote total", "g/kg"),
    "clay": ("Argile", "%"),
    "silt": ("Limon", "%"),
    "sand": ("Sable", "%"),
    "cec": ("Capacite d'echange cationique", "cmol(c)/kg"),
    "bdod": ("Densite apparente", "kg/dm3"),
}

PROFONDEURS = ["0-5cm", "5-15cm", "15-30cm"]
EPAISSEURS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}


# --------------------------------------------------------------------------
# 1. Requete SoilGrids
# --------------------------------------------------------------------------
def fetch_soilgrids(lat: float, lon: float, attempts: int = 4) -> dict | None:
    """Une requete SoilGrids, avec plusieurs essais : l'API (beta) est parfois tres lente."""
    params = [("lat", lat), ("lon", lon)]
    params += [("property", p) for p in PROPRIETES]
    params += [("depth", d) for d in PROFONDEURS]
    params += [("value", v) for v in ("mean", "Q0.05", "Q0.95")]
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(SOILGRIDS_URL, params=params, timeout=90)
            if resp.status_code == 429:  # trop de requetes : on attend avant de reessayer
                print("    limite de requetes atteinte, pause d'une minute...")
                time.sleep(60)
                continue
            if resp.status_code >= 500:
                raise requests.HTTPError(f"erreur serveur {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            wait = 20 * attempt
            print(f"    pas de reponse ({type(exc).__name__}), nouvel essai dans {wait} s "
                  f"[{attempt}/{attempts}]")
            time.sleep(wait)
    return None


def has_data(payload: dict) -> bool:
    """SoilGrids renvoie des valeurs vides (null) en ville, sur l'eau ou hors zone cartographiee."""
    for layer in payload["properties"]["layers"]:
        for depth in layer["depths"]:
            if depth["values"].get("mean") is not None:
                return True
    return False


def candidate_points(lat: float, lon: float, step: float, max_radius: float):
    """Le point demande, puis des anneaux de 8 points de plus en plus eloignes."""
    yield lat, lon
    r = step
    while r <= max_radius + 1e-9:
        for dlat, dlon in [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]:
            yield round(lat + dlat * r, 4), round(lon + dlon * r, 4)
        r += step


def distance_km(lat1, lon1, lat2, lon2) -> float:
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = rlat2 - rlat1, math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def find_soil_point(lat, lon, step, max_radius, pause=13):
    """Cherche le point le plus proche avec des donnees (pause entre requetes : limite de l'API)."""
    for i, (plat, plon) in enumerate(candidate_points(lat, lon, step, max_radius)):
        if i > 0:
            time.sleep(pause)
        print(f"  essai {i + 1} : ({plat}, {plon})")
        payload = fetch_soilgrids(plat, plon)
        if payload is None:
            print("    le serveur ne repond pas pour ce point, on passe au suivant")
            continue
        if has_data(payload):
            return payload, plat, plon
    raise SystemExit(f"Aucune donnee SoilGrids dans un rayon de {max_radius} degre. "
                     f"Donne les coordonnees d'une parcelle agricole avec --lat et --lon.")


def parse_layers(payload: dict) -> pd.DataFrame:
    """Une ligne par (propriete, profondeur), valeurs converties en unites lisibles."""
    rows = []
    for layer in payload["properties"]["layers"]:
        prop = layer["name"]
        if prop not in PROPRIETES:
            continue
        # valeur brute / d_factor = unite cible (pH, g/kg, %, cmol(c)/kg, kg/dm3)
        d_factor = layer["unit_measure"]["d_factor"] or 1
        for depth in layer["depths"]:
            values = depth["values"]

            def conv(key):
                v = values.get(key)
                return None if v is None else v / d_factor

            rows.append(
                {
                    "propriete": prop,
                    "nom": PROPRIETES[prop][0],
                    "unite": PROPRIETES[prop][1],
                    "profondeur": depth["label"],
                    "moyenne": conv("mean"),
                    "q05": conv("Q0.05"),
                    "q95": conv("Q0.95"),
                }
            )
    return pd.DataFrame(rows)


def topsoil_average(layers: pd.DataFrame) -> pd.DataFrame:
    """Moyenne ponderee par l'epaisseur de chaque couche, sur 0-30 cm."""
    df = layers.dropna(subset=["moyenne"]).copy()
    df["poids"] = df["profondeur"].map(EPAISSEURS)
    out = []
    for prop, g in df.groupby("propriete", sort=False):
        w = g["poids"]
        out.append(
            {
                "propriete": prop,
                "nom": g["nom"].iloc[0],
                "unite": g["unite"].iloc[0],
                "moyenne_0_30cm": (g["moyenne"] * w).sum() / w.sum(),
                "q05_0_30cm": (g["q05"] * w).sum() / w.sum() if g["q05"].notna().all() else None,
                "q95_0_30cm": (g["q95"] * w).sum() / w.sum() if g["q95"].notna().all() else None,
            }
        )
    return pd.DataFrame(out).set_index("propriete")


# --------------------------------------------------------------------------
# 2. Interpretation
# --------------------------------------------------------------------------
def texture_usda(sand: float, silt: float, clay: float) -> str:
    """Classe de texture du triangle USDA (en francais)."""
    if silt + 1.5 * clay < 15:
        return "Sable"
    if silt + 1.5 * clay >= 15 and silt + 2 * clay < 30:
        return "Sable limoneux"
    if (7 <= clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50 and silt + 2 * clay >= 30):
        return "Limon sableux"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return "Limon"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "Limon fin"
    if silt >= 80 and clay < 12:
        return "Limon tres fin"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "Limon argilo-sableux"
    if 27 <= clay < 40 and 20 < sand <= 45:
        return "Limon argileux"
    if 27 <= clay < 40 and sand <= 20:
        return "Limon argilo-fin"
    if clay >= 35 and sand > 45:
        return "Argile sableuse"
    if clay >= 40 and silt >= 40:
        return "Argile limoneuse"
    return "Argile"


def niveau_ph(ph: float) -> str:
    if ph < 5.0:
        return "tres acide"
    if ph < 5.5:
        return "acide"
    if ph < 6.5:
        return "legerement acide"
    if ph < 7.5:
        return "neutre"
    return "basique"


def niveau_carbone(soc_g_kg: float) -> str:
    # seuils indicatifs pour les sols tropicaux
    if soc_g_kg < 10:
        return "faible"
    if soc_g_kg < 20:
        return "moyen"
    return "eleve"


def aptitude_ph(ph: float, crop: dict) -> tuple[str, str]:
    lo = crop["ph_sol"]["optimum_min"]
    hi = crop["ph_sol"]["optimum_max"]
    if lo <= ph <= hi:
        return "bon", f"pH dans l'optimum ({lo}-{hi})"
    ecart = lo - ph if ph < lo else ph - hi
    sens = "trop acide" if ph < lo else "trop basique"
    if ecart <= 0.5:
        return "limite", f"un peu {sens} (optimum {lo}-{hi})"
    return "defavorable", f"{sens} (optimum {lo}-{hi}) : chaulage ou autre culture"


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Sol de la parcelle avec ISRIC SoilGrids")
    parser.add_argument("--lat", type=float, default=5.44)
    parser.add_argument("--lon", type=float, default=10.05)
    parser.add_argument("--name", default="dschang")
    parser.add_argument("--offline", action="store_true",
                        help="Relire la reponse deja telechargee au lieu d'appeler l'API")
    parser.add_argument("--pas", type=float, default=0.01,
                        help="Ecart entre deux essais si le point n'a pas de donnees (0.01 degre = environ 1,1 km)")
    parser.add_argument("--rayon-max", type=float, default=0.04,
                        help="Distance maximale de recherche autour du point (degres)")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"soilgrids_{args.name}.json"

    if args.offline and raw_path.exists():
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        print(f"Donnees chargees depuis {raw_path}")
    else:
        print("Interrogation de SoilGrids (si le point est en ville, recherche d'un point agricole proche)...")
        payload, _, _ = find_soil_point(args.lat, args.lon, args.pas, args.rayon_max)
        raw_path.write_text(json.dumps(payload), encoding="utf-8")
        print(f"Reponse brute enregistree : {raw_path}")

    if not has_data(payload):
        raise SystemExit("La reponse enregistree ne contient pas de donnees : relance sans --offline.")

    # point reellement utilise (donne par la reponse SoilGrids : [lon, lat])
    used_lon, used_lat = payload["geometry"]["coordinates"][:2]
    ecart_km = distance_km(args.lat, args.lon, used_lat, used_lon)

    layers = parse_layers(payload)

    top = topsoil_average(layers)
    layers.round(2).to_csv(PROCESSED_DIR / f"{args.name}_sol_par_profondeur.csv", index=False)

    ph = top.loc["phh2o", "moyenne_0_30cm"]
    soc = top.loc["soc", "moyenne_0_30cm"]
    sand, silt, clay = (top.loc[p, "moyenne_0_30cm"] for p in ("sand", "silt", "clay"))
    texture = texture_usda(sand, silt, clay)

    crops = json.loads(CROPS_PATH.read_text(encoding="utf-8"))["cultures"]
    aptitudes = []
    for crop in crops:
        niveau, detail = aptitude_ph(ph, crop)
        aptitudes.append({"culture": crop["nom"], "aptitude_ph": niveau, "detail": detail})
    aptitudes = pd.DataFrame(aptitudes)

    profil = {
        "zone": args.name,
        "latitude": round(used_lat, 4),
        "longitude": round(used_lon, 4),
        "point_demande": [args.lat, args.lon],
        "ecart_point_demande_km": round(ecart_km, 2),
        "source": "ISRIC SoilGrids v2.0 (250 m), moyenne ponderee 0-30 cm",
        "ph": round(ph, 2),
        "ph_niveau": niveau_ph(ph),
        "ph_intervalle_90pct": [round(top.loc["phh2o", "q05_0_30cm"], 2),
                                round(top.loc["phh2o", "q95_0_30cm"], 2)]
        if top.loc["phh2o", "q05_0_30cm"] is not None else None,
        "carbone_organique_g_kg": round(soc, 1),
        "carbone_niveau": niveau_carbone(soc),
        "azote_g_kg": round(top.loc["nitrogen", "moyenne_0_30cm"], 2),
        "argile_pct": round(clay, 1),
        "limon_pct": round(silt, 1),
        "sable_pct": round(sand, 1),
        "texture": texture,
        "cec_cmol_kg": round(top.loc["cec", "moyenne_0_30cm"], 1),
        "densite_apparente_kg_dm3": round(top.loc["bdod", "moyenne_0_30cm"], 2),
        "aptitude_ph_cultures": aptitudes.to_dict(orient="records"),
    }
    out_json = PROCESSED_DIR / f"{args.name}_sol.json"
    out_json.write_text(json.dumps(profil, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resume console
    print("\n===== PROFIL DU SOL (0-30 cm) =====")
    print(f"Zone : {args.name}, point utilise ({used_lat:.4f}, {used_lon:.4f}), "
          f"a {ecart_km:.1f} km du point demande")
    for prop, row in top.iterrows():
        unite = f" {row['unite']}" if row["unite"] else ""
        rng = ""
        if row["q05_0_30cm"] is not None and pd.notna(row["q05_0_30cm"]):
            rng = f"  (90 % de chances entre {row['q05_0_30cm']:.2f} et {row['q95_0_30cm']:.2f})"
        print(f"  {row['nom']:<32}: {row['moyenne_0_30cm']:.2f}{unite}{rng}")
    print(f"\npH : {ph:.1f}, {niveau_ph(ph)}")
    print(f"Carbone organique : {soc:.1f} g/kg, niveau {niveau_carbone(soc)}")
    print(f"Texture : {texture} ({sand:.0f} % sable, {silt:.0f} % limon, {clay:.0f} % argile)")
    print("\nAptitude des cultures selon le pH :")
    for _, r in aptitudes.iterrows():
        print(f"  {r['culture']:<16}: {r['aptitude_ph']:<12} {r['detail']}")
    print(f"\nProfil enregistre : {out_json}")


if __name__ == "__main__":
    main()