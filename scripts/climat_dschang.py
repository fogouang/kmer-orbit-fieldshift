"""
Kmer Orbit - Field Shift
Etape 1 : analyse climatique d'une zone pilote a partir de NASA POWER.

Ce script :
  1. telecharge les donnees journalieres NASA POWER (pluie, temperatures,
     humidite, humidite du sol) pour un point GPS ;
  2. les agrege par mois et par an ;
  3. calcule la date de debut de saison des pluies pour chaque annee ;
  4. compare les deux decennies (debut vs fin de periode) ;
  5. produit des CSV et des graphiques prets pour le pitch.

Usage :
    pip install requests pandas matplotlib
    python scripts/climat_dschang.py
    python scripts/climat_dschang.py --lat 5.44 --lon 10.05 --start 2005 --end 2024 --name dschang
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Variables NASA POWER (communaute AG = agriculture)
PARAMETERS = {
    "PRECTOTCORR": "pluie_mm",          # precipitations corrigees, mm/jour
    "T2M": "temp_moy_c",                # temperature moyenne a 2 m
    "T2M_MAX": "temp_max_c",
    "T2M_MIN": "temp_min_c",
    "RH2M": "humidite_air_pct",         # humidite relative a 2 m
    "GWETROOT": "humidite_sol_racines", # humidite du sol zone racinaire (0 = sec, 1 = sature)
}

MOIS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aout", "Sep", "Oct", "Nov", "Dec"]

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "docs" / "figures"


# --------------------------------------------------------------------------
# 1. Telechargement
# --------------------------------------------------------------------------
def fetch_power_daily(lat: float, lon: float, start_year: int, end_year: int) -> dict:
    """Interroge l'API NASA POWER (pas besoin de compte)."""
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": f"{start_year}0101",
        "end": f"{end_year}1231",
        "format": "JSON",
    }
    resp = requests.get(POWER_URL, params=params, timeout=180)
    resp.raise_for_status()
    return resp.json()


def power_json_to_dataframe(payload: dict) -> pd.DataFrame:
    """Transforme la reponse JSON en tableau journalier propre."""
    data = payload["properties"]["parameter"]
    fill_value = payload.get("header", {}).get("fill_value", -999.0)

    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"
    df = df.rename(columns=PARAMETERS)
    df = df.astype("float64").replace(fill_value, float("nan"))
    return df.sort_index()


# --------------------------------------------------------------------------
# 2. Agregations
# --------------------------------------------------------------------------
def monthly_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Pluie en cumul mensuel, autres variables en moyenne."""
    agg = {col: "mean" for col in daily.columns}
    agg["pluie_mm"] = "sum"
    monthly = daily.resample("MS").agg(agg)
    monthly["annee"] = monthly.index.year
    monthly["mois"] = monthly.index.month
    return monthly


def yearly_summary(daily: pd.DataFrame, onsets: pd.DataFrame) -> pd.DataFrame:
    yearly = pd.DataFrame(
        {
            "pluie_totale_mm": daily["pluie_mm"].resample("YS").sum(),
            "temp_moy_c": daily["temp_moy_c"].resample("YS").mean(),
            "temp_max_moy_c": daily["temp_max_c"].resample("YS").mean(),
            "jours_de_pluie": (daily["pluie_mm"] >= 1).resample("YS").sum(),
            "humidite_sol_moy": daily["humidite_sol_racines"].resample("YS").mean(),
        }
    )
    yearly.index = yearly.index.year
    yearly.index.name = "annee"
    return yearly.join(onsets)


# --------------------------------------------------------------------------
# 3. Debut de la saison des pluies
# --------------------------------------------------------------------------
def rainy_season_onset(
    daily: pd.DataFrame,
    search_from: str = "02-15",
    cumul_mm: float = 20.0,
    cumul_days: int = 3,
    dry_spell_days: int = 7,
    check_days: int = 30,
) -> pd.DataFrame:
    """
    Definition agronomique classique (simplifiee) :
    le debut de saison est le premier jour, apres `search_from`, ou
      - la pluie cumulee sur `cumul_days` jours atteint `cumul_mm`,
      - et ou il n'y a pas de sequence seche de `dry_spell_days` jours
        (pluie < 1 mm) dans les `check_days` jours suivants.
    C'est ce qui compte pour l'agriculteur : semer sans que les jeunes
    plants meurent d'une secheresse juste apres.
    """
    rain = daily["pluie_mm"].fillna(0)
    results = []

    for year in sorted(rain.index.year.unique()):
        year_rain = rain[rain.index.year == year]
        start = pd.Timestamp(f"{year}-{search_from}")
        candidates = year_rain[year_rain.index >= start]
        rolling = rain.rolling(cumul_days).sum()

        onset = None
        for day in candidates.index:
            if rolling.get(day, 0) < cumul_mm:
                continue
            following = rain[day + pd.Timedelta(days=1): day + pd.Timedelta(days=check_days)]
            if len(following) < check_days:
                break
            dry = (following < 1).astype(int)
            longest_dry = dry.groupby((dry == 0).cumsum()).sum().max()
            if longest_dry < dry_spell_days:
                onset = day
                break

        results.append(
            {
                "annee": year,
                "debut_saison": onset.date().isoformat() if onset else None,
                "debut_saison_jour": onset.day_of_year if onset else None,
            }
        )

    return pd.DataFrame(results).set_index("annee")


# --------------------------------------------------------------------------
# 4. Comparaison des deux decennies
# --------------------------------------------------------------------------
def compare_periods(monthly: pd.DataFrame, split_year: int) -> pd.DataFrame:
    before = monthly[monthly["annee"] < split_year]
    after = monthly[monthly["annee"] >= split_year]
    label_a = f"{before['annee'].min()}-{before['annee'].max()}"
    label_b = f"{after['annee'].min()}-{after['annee'].max()}"

    comp = pd.DataFrame(
        {
            f"pluie_{label_a}": before.groupby("mois")["pluie_mm"].mean(),
            f"pluie_{label_b}": after.groupby("mois")["pluie_mm"].mean(),
            f"temp_{label_a}": before.groupby("mois")["temp_moy_c"].mean(),
            f"temp_{label_b}": after.groupby("mois")["temp_moy_c"].mean(),
        }
    )
    comp["ecart_pluie_pct"] = (
        (comp[f"pluie_{label_b}"] - comp[f"pluie_{label_a}"]) / comp[f"pluie_{label_a}"] * 100
    )
    comp["ecart_temp_c"] = comp[f"temp_{label_b}"] - comp[f"temp_{label_a}"]
    comp.index = MOIS
    comp.index.name = "mois"
    return comp.round(2), label_a, label_b


# --------------------------------------------------------------------------
# 5. Graphiques
# --------------------------------------------------------------------------
def plot_rain_comparison(comp, label_a, label_b, name, out: Path):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(12)
    w = 0.4
    ax.bar([i - w / 2 for i in x], comp[f"pluie_{label_a}"], w, label=label_a, color="#9DB4C0")
    ax.bar([i + w / 2 for i in x], comp[f"pluie_{label_b}"], w, label=label_b, color="#1F6F50")
    ax.set_xticks(list(x), MOIS)
    ax.set_ylabel("Pluie moyenne (mm/mois)")
    ax.set_title(f"{name.title()} : pluie mensuelle, {label_a} vs {label_b} (NASA POWER)")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_yearly(yearly: pd.DataFrame, name: str, out: Path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    axes[0].bar(yearly.index, yearly["pluie_totale_mm"], color="#1F6F50")
    axes[0].set_ylabel("Pluie annuelle (mm)")

    axes[1].plot(yearly.index, yearly["temp_moy_c"], marker="o", color="#C0392B")
    axes[1].set_ylabel("Temp. moyenne (°C)")

    onset = yearly["debut_saison_jour"].astype("float")
    axes[2].plot(yearly.index, onset, marker="o", color="#2E86C1")
    axes[2].set_ylabel("Début des pluies\n(jour de l'année)")
    axes[2].invert_yaxis()  # plus haut = plus tot
    axes[2].xaxis.set_major_locator(MaxNLocator(integer=True))

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_title(f"{name.title()} : évolution annuelle (NASA POWER)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Analyse climatique NASA POWER d'une zone pilote")
    parser.add_argument("--lat", type=float, default=5.44)
    parser.add_argument("--lon", type=float, default=10.05)
    parser.add_argument("--start", type=int, default=2005)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--name", default="dschang")
    parser.add_argument("--offline", action="store_true",
                        help="Reutiliser le JSON brut deja telecharge au lieu d'appeler l'API")
    args = parser.parse_args()

    for d in (RAW_DIR, PROCESSED_DIR, FIG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / f"power_{args.name}_{args.start}_{args.end}.json"

    if args.offline and raw_path.exists():
        payload = json.loads(raw_path.read_text())
        print(f"Donnees chargees depuis {raw_path}")
    else:
        print("Telechargement NASA POWER (peut prendre 30 s a 1 min)...")
        payload = fetch_power_daily(args.lat, args.lon, args.start, args.end)
        raw_path.write_text(json.dumps(payload))
        print(f"Donnees brutes enregistrees : {raw_path}")

    daily = power_json_to_dataframe(payload)
    monthly = monthly_summary(daily)
    onsets = rainy_season_onset(daily)
    yearly = yearly_summary(daily, onsets)

    split_year = args.start + (args.end - args.start + 1) // 2
    comp, label_a, label_b = compare_periods(monthly, split_year)

    daily.to_csv(PROCESSED_DIR / f"{args.name}_journalier.csv")
    monthly.to_csv(PROCESSED_DIR / f"{args.name}_mensuel.csv")
    yearly.to_csv(PROCESSED_DIR / f"{args.name}_annuel.csv")
    comp.to_csv(PROCESSED_DIR / f"{args.name}_comparaison_decennies.csv")

    plot_rain_comparison(comp, label_a, label_b, args.name,
                         FIG_DIR / f"{args.name}_pluie_decennies.png")
    plot_yearly(yearly, args.name, FIG_DIR / f"{args.name}_evolution_annuelle.png")

    # Resume console
    pa = yearly.loc[yearly.index < split_year]
    pb = yearly.loc[yearly.index >= split_year]
    print("\n===== RESUME =====")
    print(f"Zone : {args.name} ({args.lat}, {args.lon}), {args.start}-{args.end}")
    print(f"Pluie annuelle moyenne : {pa['pluie_totale_mm'].mean():.0f} mm ({label_a}) "
          f"-> {pb['pluie_totale_mm'].mean():.0f} mm ({label_b})")
    print(f"Temperature moyenne : {pa['temp_moy_c'].mean():.2f} °C -> {pb['temp_moy_c'].mean():.2f} °C")
    print(f"Debut des pluies (jour moyen) : {pa['debut_saison_jour'].astype(float).mean():.0f} "
          f"-> {pb['debut_saison_jour'].astype(float).mean():.0f}")
    print("\nEcart de pluie par mois (%) :")
    print(comp["ecart_pluie_pct"].to_string())
    print(f"\nCSV : {PROCESSED_DIR}")
    print(f"Graphiques : {FIG_DIR}")


if __name__ == "__main__":
    main()