"""
Kmer Orbit - Field Shift
Etape 2 : recouper la pluie NASA POWER avec GPM IMERG (V07, mensuel).

GPM IMERG est le produit de reference de la NASA pour la pluie par satellite
(grille de 0,1 degre, soit environ 11 km). On l'utilise ici pour verifier si
les annees tres humides vues dans NASA POWER (2015-2022) sont reelles.

Ce script :
  1. se connecte a NASA Earthdata (ton compte, avec GES DISC autorise) ;
  2. lit, pour chaque mois, seulement les pixels IMERG autour de la zone
     (pas de telechargement des fichiers mondiaux complets) ;
  3. compare mois par mois et annee par annee avec NASA POWER ;
  4. produit des CSV et deux graphiques.

Prerequis :
  - avoir lance scripts/climat_dschang.py (il produit data/processed/dschang_mensuel.csv)
  - uv add earthaccess xarray h5netcdf

Usage :
    uv run scripts/imerg_dschang.py
    uv run scripts/imerg_dschang.py --lat 5.44 --lon 10.05 --start 2005 --end 2024 --name dschang

Au premier lancement, earthaccess demande ton identifiant et ton mot de passe
Earthdata, puis les enregistre (fichier .netrc) pour les fois suivantes.
Les mois deja lus sont gardes en cache : si le script s'arrete, relance-le,
il reprend la ou il en etait.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "docs" / "figures"

IMERG_SHORT_NAME = "GPM_3IMERGM"  # IMERG Final Run, mensuel
IMERG_VERSION = "07"


# --------------------------------------------------------------------------
# 1. Lecture IMERG (seulement les pixels utiles)
# --------------------------------------------------------------------------
def granule_month(granule) -> pd.Timestamp:
    begin = granule["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
    return pd.Timestamp(begin[:10]).to_period("M").to_timestamp()


def fetch_imerg_monthly(lat: float, lon: float, start: int, end: int,
                        box: float, cache_path: Path) -> pd.DataFrame:
    import earthaccess
    import xarray as xr

    cache = (
        pd.read_csv(cache_path, parse_dates=["date"]).set_index("date")
        if cache_path.exists()
        else pd.DataFrame(columns=["pluie_mm"], index=pd.DatetimeIndex([], name="date"))
    )

    earthaccess.login(strategy="all", persist=True)

    granules = earthaccess.search_data(
        short_name=IMERG_SHORT_NAME,
        version=IMERG_VERSION,
        temporal=(f"{start}-01-01", f"{end}-12-31"),
        bounding_box=(lon - box, lat - box, lon + box, lat + box),
    )
    todo = [g for g in granules if granule_month(g) not in cache.index]
    print(f"{len(granules)} mois trouves, {len(granules) - len(todo)} deja en cache, "
          f"{len(todo)} a lire.")

    for i, granule in enumerate(todo, 1):
        month = granule_month(granule)
        fileobj = earthaccess.open([granule], show_progress=False)[0]
        with xr.open_dataset(fileobj, engine="h5netcdf", group="Grid", decode_times=False) as ds:
            zone = ds["precipitation"].sel(
                lat=slice(lat - box, lat + box),
                lon=slice(lon - box, lon + box),
            )
            rate_mm_per_hour = float(zone.mean())
        hours = month.days_in_month * 24
        cache.loc[month, "pluie_mm"] = rate_mm_per_hour * hours

        # sauvegarde au fil de l'eau pour pouvoir reprendre
        cache.sort_index().to_csv(cache_path)
        print(f"  [{i}/{len(todo)}] {month:%Y-%m} : {cache.loc[month, 'pluie_mm']:.0f} mm")

    cache = cache.sort_index()
    cache.index.name = "date"
    return cache[(cache.index.year >= start) & (cache.index.year <= end)].astype(float)


# --------------------------------------------------------------------------
# 2. Comparaison avec NASA POWER
# --------------------------------------------------------------------------
def compare_with_power(imerg: pd.DataFrame, power_monthly_csv: Path):
    power = pd.read_csv(power_monthly_csv, parse_dates=["date"]).set_index("date")

    monthly = pd.DataFrame(
        {
            "pluie_power_mm": power["pluie_mm"],
            "pluie_imerg_mm": imerg["pluie_mm"],
        }
    ).dropna()
    monthly["annee"] = monthly.index.year
    monthly["mois"] = monthly.index.month

    yearly = monthly.groupby("annee")[["pluie_power_mm", "pluie_imerg_mm"]].sum()
    yearly["ecart_pct"] = (
        (yearly["pluie_power_mm"] - yearly["pluie_imerg_mm"]) / yearly["pluie_imerg_mm"] * 100
    )
    return monthly, yearly.round(1)


# --------------------------------------------------------------------------
# 3. Graphiques
# --------------------------------------------------------------------------
def plot_yearly_comparison(yearly: pd.DataFrame, name: str, out: Path):
    fig, ax = plt.subplots(figsize=(11, 5))
    w = 0.4
    x = yearly.index
    ax.bar(x - w / 2, yearly["pluie_power_mm"], w, label="NASA POWER", color="#9DB4C0")
    ax.bar(x + w / 2, yearly["pluie_imerg_mm"], w, label="GPM IMERG", color="#1F6F50")
    ax.set_ylabel("Pluie annuelle (mm)")
    ax.set_title(f"{name.title()} : pluie annuelle, NASA POWER vs GPM IMERG")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_monthly_scatter(monthly: pd.DataFrame, name: str, out: Path):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(monthly["pluie_imerg_mm"], monthly["pluie_power_mm"], s=14, alpha=0.6, color="#1F6F50")
    lim = max(monthly["pluie_imerg_mm"].max(), monthly["pluie_power_mm"].max()) * 1.05
    ax.plot([0, lim], [0, lim], color="#7F7F7F", linestyle="--", linewidth=1, label="Accord parfait")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("GPM IMERG (mm/mois)")
    ax.set_ylabel("NASA POWER (mm/mois)")
    ax.set_title(f"{name.title()} : pluie mensuelle, une source contre l'autre")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Recoupement pluie NASA POWER / GPM IMERG")
    parser.add_argument("--lat", type=float, default=5.44)
    parser.add_argument("--lon", type=float, default=10.05)
    parser.add_argument("--start", type=int, default=2005)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--name", default="dschang")
    parser.add_argument("--box", type=float, default=0.15,
                        help="Demi-largeur de la zone en degres (0.15 = environ 3x3 pixels IMERG)")
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    power_csv = PROCESSED_DIR / f"{args.name}_mensuel.csv"
    if not power_csv.exists():
        raise SystemExit(f"{power_csv} introuvable : lance d'abord scripts/climat_dschang.py")

    cache_path = PROCESSED_DIR / f"{args.name}_imerg_mensuel.csv"
    imerg = fetch_imerg_monthly(args.lat, args.lon, args.start, args.end, args.box, cache_path)

    monthly, yearly = compare_with_power(imerg, power_csv)
    monthly.to_csv(PROCESSED_DIR / f"{args.name}_power_vs_imerg_mensuel.csv")
    yearly.to_csv(PROCESSED_DIR / f"{args.name}_power_vs_imerg_annuel.csv")

    plot_yearly_comparison(yearly, args.name, FIG_DIR / f"{args.name}_power_vs_imerg_annuel.png")
    plot_monthly_scatter(monthly, args.name, FIG_DIR / f"{args.name}_power_vs_imerg_mensuel.png")

    # Resume console
    split = args.start + (args.end - args.start + 1) // 2
    a = yearly[yearly.index < split]
    b = yearly[yearly.index >= split]
    corr = monthly["pluie_power_mm"].corr(monthly["pluie_imerg_mm"])

    print("\n===== RESUME =====")
    print(f"Mois compares : {len(monthly)}")
    print(f"Correlation mensuelle POWER / IMERG : {corr:.2f}")
    print(f"Pluie annuelle moyenne POWER : {a['pluie_power_mm'].mean():.0f} mm ({args.start}-{split - 1}) "
          f"-> {b['pluie_power_mm'].mean():.0f} mm ({split}-{args.end})")
    print(f"Pluie annuelle moyenne IMERG : {a['pluie_imerg_mm'].mean():.0f} mm ({args.start}-{split - 1}) "
          f"-> {b['pluie_imerg_mm'].mean():.0f} mm ({split}-{args.end})")
    print("\nPar annee (mm) :")
    print(yearly.to_string())
    print(f"\nCSV : {PROCESSED_DIR}")
    print(f"Graphiques : {FIG_DIR}")


if __name__ == "__main__":
    main()