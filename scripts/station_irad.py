"""
Kmer Orbit - Field Shift
Etape 6 : VALIDATION AU SOL avec la station meteo de l'IRAD Dschang.

Compare les mesures de la station (pluie et temperature mensuelles, fournies par
l'IRAD) aux donnees satellite utilisees par le moteur :
  - pluie : GPM IMERG (retenu) et NASA POWER (ecarte pour la pluie) ;
  - temperature : NASA POWER T2M.

Entree  : data/raw/irad_dschang_meteo.csv (transcription du PDF IRAD)
Sorties : data/processed/<zone>_station_mensuel.csv          (donnees station + controles qualite)
          data/processed/<zone>_station_vs_satellite.csv     (mois communs station / IMERG / POWER)
          data/processed/<zone>_station_validation.json      (correlation, biais, erreurs)
          figures/<zone>_station_vs_satellite.png

Usage :
    uv run scripts/station_irad.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "irad_dschang_meteo.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "figures"

ECART_TEMP_SUSPECT = 3.0   # °C d'ecart a la mediane du meme mois sur toutes les annees
REPETITIONS_SUSPECTES = 4  # meme valeur exacte repetee au moins 4 fois dans l'annee
MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


# --------------------------------------------------------------------------
# 1. Donnees station + controle qualite
# --------------------------------------------------------------------------
def charger_station() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    df["date"] = pd.to_datetime(dict(year=df.annee, month=df.mois, day=1))
    return df.set_index("date")


def controler(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des colonnes de controle : on garde les valeurs, on les signale."""
    df = df.copy()
    df["alerte_pluie"] = ""
    df["alerte_temperature"] = ""

    # Pluie : nombre de jours de pluie incoherent avec le total
    incoherent = (df.jours_pluie == 0) & (df.pluie_mm > 0)
    df.loc[incoherent, "alerte_pluie"] = "pluie notee sans jour de pluie"
    faible = (df.jours_pluie >= 10) & (df.pluie_mm < 2 * df.jours_pluie)
    df.loc[faible, "alerte_pluie"] = "total tres faible pour le nombre de jours de pluie"

    # Temperature : ecart anormal a la mediane du mois
    mediane = df.groupby("mois")["temperature_c"].transform("median")
    ecart = (df.temperature_c - mediane).abs() > ECART_TEMP_SUSPECT
    df.loc[ecart, "alerte_temperature"] = "ecart anormal a la normale du mois"

    # Temperature : meme valeur recopiee plusieurs fois dans l'annee
    for annee, groupe in df.groupby("annee"):
        comptes = groupe.temperature_c.value_counts()
        repetees = comptes[comptes >= REPETITIONS_SUSPECTES].index
        masque = (df.annee == annee) & df.temperature_c.isin(repetees) & (df.alerte_temperature == "")
        df.loc[masque, "alerte_temperature"] = "valeur identique repetee (arrondie ou recopiee ?)"
    return df


# --------------------------------------------------------------------------
# 2. Comparaison avec le satellite
# --------------------------------------------------------------------------
def statistiques(obs: pd.Series, sat: pd.Series) -> dict:
    paire = pd.concat([obs, sat], axis=1, keys=["obs", "sat"]).dropna()
    erreur = paire.sat - paire.obs
    return {
        "nb_mois": int(len(paire)),
        "correlation": round(float(paire.obs.corr(paire.sat)), 2),
        "biais_moyen": round(float(erreur.mean()), 1),
        "biais_pct": round(float(100 * erreur.sum() / paire.obs.sum()), 1) if paire.obs.sum() else None,
        "erreur_absolue_moyenne": round(float(erreur.abs().mean()), 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Validation des donnees satellite par la station IRAD")
    parser.add_argument("--name", default="dschang")
    args = parser.parse_args()

    station = controler(charger_station())
    station.drop(columns=["annee", "mois"]).to_csv(PROCESSED_DIR / f"{args.name}_station_mensuel.csv")

    imerg = pd.read_csv(PROCESSED_DIR / f"{args.name}_imerg_mensuel.csv", parse_dates=["date"]).set_index("date")["pluie_mm"]
    power = pd.read_csv(PROCESSED_DIR / f"{args.name}_mensuel.csv", parse_dates=["date"]).set_index("date")

    comp = pd.DataFrame({
        "station_pluie_mm": station.pluie_mm,
        "imerg_pluie_mm": imerg,
        "power_pluie_mm": power.pluie_mm,
        "station_temp_c": station.temperature_c,
        "power_temp_c": power.temp_moy_c,
        "alerte_pluie": station.alerte_pluie,
        "alerte_temperature": station.alerte_temperature,
    }).loc[station.index]
    comp.round(2).to_csv(PROCESSED_DIR / f"{args.name}_station_vs_satellite.csv")

    # Pluie : on exclut les mois signales
    pluie_ok = comp[comp.alerte_pluie == ""]
    # Temperature : on exclut les mois signales
    temp_ok = comp[comp.alerte_temperature == ""]

    # Totaux annuels (toutes les annees de pluie ont 12 mois)
    annuel = comp[["station_pluie_mm", "imerg_pluie_mm", "power_pluie_mm"]].groupby(comp.index.year).sum(min_count=12).dropna()

    # Saison par saison (memes mois que le moteur)
    saisons = {"saison_1": [3, 4, 5, 6, 7], "saison_2": [8, 9, 10, 11]}
    par_saison = {}
    for s, mois in saisons.items():
        sel = comp[comp.index.month.isin(mois)]
        tot = sel[["station_pluie_mm", "imerg_pluie_mm"]].groupby(sel.index.year).sum(min_count=len(mois)).dropna()
        par_saison[s] = {
            "station_moyenne_mm": round(float(tot.station_pluie_mm.mean()), 0),
            "imerg_moyenne_mm": round(float(tot.imerg_pluie_mm.mean()), 0),
            "ecart_pct": round(float(100 * (tot.imerg_pluie_mm.mean() / tot.station_pluie_mm.mean() - 1)), 1),
        }

    resultats = {
        "station": "IRAD Dschang (donnees fournies par la station)",
        "periode_pluie": f"{station.pluie_mm.dropna().index.year.min()}-{station.pluie_mm.dropna().index.year.max()}, sans 2018",
        "pluie_mensuelle": {
            "imerg": statistiques(pluie_ok.station_pluie_mm, pluie_ok.imerg_pluie_mm),
            "power": statistiques(pluie_ok.station_pluie_mm, pluie_ok.power_pluie_mm),
        },
        "pluie_annuelle": {
            "station_moyenne_mm": round(float(annuel.station_pluie_mm.mean()), 0),
            "imerg_moyenne_mm": round(float(annuel.imerg_pluie_mm.mean()), 0),
            "power_moyenne_mm": round(float(annuel.power_pluie_mm.mean()), 0),
            "par_annee": {int(a): {k: round(float(v), 0) for k, v in r.items()} for a, r in annuel.iterrows()},
        },
        "pluie_par_saison": par_saison,
        "temperature_mensuelle_power": statistiques(temp_ok.station_temp_c, temp_ok.power_temp_c),
        "mois_signales": {
            "pluie": [f"{d:%Y-%m} : {a}" for d, a in comp.alerte_pluie.items() if a],
            "temperature": [f"{d:%Y-%m} : {a}" for d, a in comp.alerte_temperature.items() if a],
        },
    }
    (PROCESSED_DIR / f"{args.name}_station_validation.json").write_text(
        json.dumps(resultats, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- Resume console ----------------
    pm = resultats["pluie_mensuelle"]
    print("===== PLUIE : satellite vs station IRAD =====")
    for src in ("imerg", "power"):
        s = pm[src]
        print(f"{src.upper():6s} : correlation {s['correlation']:.2f} | biais {s['biais_pct']:+.0f} % "
              f"| erreur moyenne {s['erreur_absolue_moyenne']:.0f} mm/mois ({s['nb_mois']} mois)")
    pa = resultats["pluie_annuelle"]
    print(f"Pluie annuelle moyenne : station {pa['station_moyenne_mm']:.0f} mm | IMERG {pa['imerg_moyenne_mm']:.0f} mm "
          f"| POWER {pa['power_moyenne_mm']:.0f} mm")
    for s, v in par_saison.items():
        print(f"  {s.replace('_', ' ')} : station {v['station_moyenne_mm']:.0f} mm, IMERG {v['imerg_moyenne_mm']:.0f} mm "
              f"({v['ecart_pct']:+.0f} %)")
    t = resultats["temperature_mensuelle_power"]
    print(f"\n===== TEMPERATURE : POWER vs station =====\ncorrelation {t['correlation']:.2f} | biais {t['biais_moyen']:+.1f} °C "
          f"| erreur moyenne {t['erreur_absolue_moyenne']:.1f} °C ({t['nb_mois']} mois fiables)")
    print(f"\nMois signales : {len(resultats['mois_signales']['pluie'])} en pluie, "
          f"{len(resultats['mois_signales']['temperature'])} en temperature")
    for m in resultats["mois_signales"]["pluie"]:
        print(f"  pluie       {m}")

    # ---------------- Figure ----------------
    FIG_DIR.mkdir(exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    clim = comp.groupby(comp.index.month)[["station_pluie_mm", "imerg_pluie_mm", "power_pluie_mm"]].mean()
    x = range(12)
    ax1.bar([i - 0.27 for i in x], clim.station_pluie_mm, 0.27, label="Station IRAD", color="#5b4636")
    ax1.bar(list(x), clim.imerg_pluie_mm, 0.27, label="GPM IMERG", color="#1f6f50")
    ax1.bar([i + 0.27 for i in x], clim.power_pluie_mm, 0.27, label="NASA POWER", color="#a9bcc6")
    ax1.set_xticks(list(x), MOIS_COURTS)
    ax1.set_ylabel("mm par mois")
    ax1.set_title("Pluie moyenne par mois (années communes)")
    ax1.legend(frameon=False)
    ax1.spines[["top", "right"]].set_visible(False)

    ax2.scatter(pluie_ok.station_pluie_mm, pluie_ok.imerg_pluie_mm, s=18, color="#1f6f50",
                label=f"IMERG (r = {pm['imerg']['correlation']:.2f})")
    ax2.scatter(pluie_ok.station_pluie_mm, pluie_ok.power_pluie_mm, s=18, color="#a9bcc6", marker="^",
                label=f"POWER (r = {pm['power']['correlation']:.2f})")
    lim = float(max(pluie_ok[["station_pluie_mm", "imerg_pluie_mm", "power_pluie_mm"]].max())) * 1.05
    ax2.plot([0, lim], [0, lim], color="#8a8a8a", lw=1, ls="--")
    ax2.set_xlim(0, lim)
    ax2.set_ylim(0, lim)
    ax2.set_xlabel("Station IRAD (mm/mois)")
    ax2.set_ylabel("Satellite (mm/mois)")
    ax2.set_title("Chaque point = un mois")
    ax2.legend(frameon=False)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = FIG_DIR / f"{args.name}_station_vs_satellite.png"
    fig.savefig(out, dpi=150)
    print(f"\nFigure : {out}")


if __name__ == "__main__":
    main()
