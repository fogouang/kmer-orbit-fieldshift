"""
Kmer Orbit - Field Shift
Etape 3 : pluie JOURNALIERE GPM IMERG (V07) pour recalculer, avec une
source fiable :
  - la date de debut de la saison des pluies, annee par annee ;
  - la comparaison mois par mois des deux decennies.

Pourquoi : le recoupement (etape 2) a montre que la pluie NASA POWER est
biaisee sur 2015-2022. Tout ce qui etait calcule a partir de la pluie POWER
doit donc etre refait avec IMERG.

Ce script :
  1. cherche les fichiers IMERG journaliers (GPM_3IMERGDF) annee par annee ;
  2. lit seulement les pixels autour de la zone via OPeNDAP DAP4 (serveur
     cloud de la NASA) : une petite requete par jour au lieu d'ouvrir chaque
     fichier mondial, en parallele ;
  3. garde chaque jour lu en cache : si le script s'arrete, relance-le ;
  4. recalcule le debut de saison et la comparaison des decennies ;
  5. compare avec ce que donnait NASA POWER.

Prerequis :
  - scripts/climat_dschang.py deja lance (pour la comparaison avec POWER)
  - scripts/imerg_dschang.py deja lance (pluie IMERG mensuelle + identifiants Earthdata)

Usage :
    uv run scripts/imerg_journalier.py
    uv run scripts/imerg_journalier.py --workers 8
    uv run scripts/imerg_journalier.py --start 2005 --end 2024 --name dschang

Par defaut, seuls les mois de fevrier a juin sont lus (environ 3 000 petites
requetes) : c'est la periode ou se cherche le debut de saison. La comparaison
des decennies utilise la pluie IMERG mensuelle deja recuperee a l'etape 2.
Tu peux l'arreter (Ctrl+C) et le relancer quand tu veux : les jours deja lus
sont gardes.
"""

from __future__ import annotations

import argparse
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

from climat_dschang import MOIS, rainy_season_onset

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "docs" / "figures"

IMERG_DAILY_SHORT_NAME = "GPM_3IMERGDF"  # IMERG Final Run, journalier
IMERG_VERSION = "07"

MOIS_ACCENTS = ["Janv.", "Févr.", "Mars", "Avril", "Mai", "Juin",
                "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]


# --------------------------------------------------------------------------
# 1. Lecture d'un jour via OPeNDAP (seulement les pixels utiles)
# --------------------------------------------------------------------------
# Grille IMERG : 0,1 degre, centres de -179.95 a 179.95 (lon) et -89.95 a 89.95 (lat)
def grid_index(value: float, origin: float) -> int:
    return int(round((value - origin) / 0.1))


def pixel_ranges(lat: float, lon: float, box: float) -> dict:
    return {
        "lat": (grid_index(lat - box, -89.95), grid_index(lat + box, -89.95)),
        "lon": (grid_index(lon - box, -179.95), grid_index(lon + box, -179.95)),
    }


def opendap_url(granule) -> str | None:
    """Lien OPeNDAP du fichier (donne par le catalogue CMR), sinon deduit du lien direct."""
    for link in granule["umm"].get("RelatedUrls", []):
        if link.get("Subtype") == "OPENDAP DATA":
            return link["URL"].removesuffix(".html")
    links = [u for u in granule.data_links(access="external") if u.endswith(".nc4")]
    return links[0].replace("/data/", "/opendap/", 1) if links else None


def dimension_order(session, url: str) -> list[str]:
    """Lit la structure du fichier (DAP4 .dmr) pour connaitre l'ordre des dimensions."""
    resp = session.get(url + ".dmr.xml", timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur {resp.status_code} sur {resp.url}\n{resp.text[:800]}")
    block = re.search(r'<Float32 name="precipitation">(.*?)</Float32>', resp.text, re.S)
    dims = re.findall(r'<Dim name="/?(\w+)"', block.group(1)) if block else []
    if len(dims) != 3:
        raise RuntimeError(f"Structure inattendue du fichier IMERG :\n{resp.text[:800]}")
    return dims


def build_constraint(dims: list[str], ranges: dict) -> str:
    """Contrainte DAP4 : seulement les pixels de la zone, pour le jour du fichier."""
    parts = []
    for d in dims:
        if d == "time":
            parts.append("[0:0]")
        else:
            a, b = ranges[d]
            parts.append(f"[{a}:{b}]")
    return "/precipitation" + "".join(parts)


def parse_nc4(content: bytes) -> float | None:
    """Moyenne des pixels renvoyes (petit fichier netCDF4), hors valeurs manquantes."""
    import io

    import numpy as np
    import xarray as xr

    with xr.open_dataset(io.BytesIO(content), engine="h5netcdf", decode_times=False) as ds:
        name = next(v for v in ds.data_vars if "precipitation" in v)
        values = ds[name].values.astype("float64").ravel()
    values = values[np.isfinite(values) & (values >= 0)]  # valeurs manquantes : -9999.9
    return float(values.mean()) if values.size else None


def read_day(session, day: str, url: str, constraint: str):
    for attempt in range(4):
        try:
            resp = session.get(url + ".dap.nc4", params={"dap4.ce": constraint}, timeout=90)
            resp.raise_for_status()
            return day, parse_nc4(resp.content)
        except Exception:
            time.sleep(3 * (attempt + 1))
    return day, None


# --------------------------------------------------------------------------
# 2. Recuperation annee par annee, avec cache
# --------------------------------------------------------------------------
def granule_day(granule) -> str:
    begin = granule["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
    return begin[:10]


def load_cache(cache_path: Path) -> pd.Series:
    if cache_path.exists():
        cache = pd.read_csv(cache_path, parse_dates=["date"]).set_index("date")["pluie_mm"]
        return cache.dropna()
    return pd.Series(dtype="float64", name="pluie_mm", index=pd.DatetimeIndex([], name="date"))


def save_cache(cache: pd.Series, cache_path: Path):
    cache.sort_index().rename("pluie_mm").to_frame().to_csv(cache_path, index_label="date")


def fetch_imerg_daily(lat, lon, start, end, box, workers, months, cache_path: Path) -> pd.Series:
    import earthaccess

    earthaccess.login(strategy="all", persist=True)
    session = earthaccess.get_requests_https_session()
    cache = load_cache(cache_path)
    ranges = pixel_ranges(lat, lon, box)
    constraint = None

    for year in range(start, end + 1):
        granules = earthaccess.search_data(
            short_name=IMERG_DAILY_SHORT_NAME,
            version=IMERG_VERSION,
            temporal=(f"{year}-01-01", f"{year}-12-31"),
            bounding_box=(lon - box, lat - box, lon + box, lat + box),
        )
        todo = []
        for g in granules:
            day = granule_day(g)
            url = opendap_url(g)
            ts = pd.Timestamp(day)
            if url and ts.month in months and ts not in cache.index:
                todo.append((day, url))

        if not todo:
            print(f"{year} : deja en cache")
            continue

        if constraint is None:
            dims = dimension_order(session, todo[0][1])
            constraint = build_constraint(dims, ranges)
            print(f"Ordre des dimensions : {dims} ; requete : {constraint}")

        t0 = time.time()
        failed = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(read_day, session, day, url, constraint) for day, url in todo]
            for n, fut in enumerate(as_completed(futures), 1):
                day, value = fut.result()
                if value is None:
                    failed += 1
                else:
                    cache.loc[pd.Timestamp(day)] = value
                if n % 50 == 0:
                    save_cache(cache, cache_path)
                    print(f"  {year} : {n}/{len(todo)} jours lus", end="\r")

        save_cache(cache, cache_path)
        msg = f"{year} : {len(todo) - failed}/{len(todo)} jours lus en {time.time() - t0:.0f} s"
        if failed:
            msg += f" ({failed} echecs, relance le script pour les recuperer)"
        print(msg + " " * 10)

    cache = cache.sort_index()
    return cache[(cache.index.year >= start) & (cache.index.year <= end)]


# --------------------------------------------------------------------------
# 3. Analyses
# --------------------------------------------------------------------------
def compare_decades(daily_rain: pd.Series, split_year: int):
    monthly = daily_rain.resample("MS").sum().to_frame("pluie_mm")
    monthly["annee"] = monthly.index.year
    monthly["mois"] = monthly.index.month
    a = monthly[monthly["annee"] < split_year]
    b = monthly[monthly["annee"] >= split_year]
    label_a = f"{a['annee'].min()}-{a['annee'].max()}"
    label_b = f"{b['annee'].min()}-{b['annee'].max()}"
    comp = pd.DataFrame(
        {
            f"pluie_{label_a}": a.groupby("mois")["pluie_mm"].mean(),
            f"pluie_{label_b}": b.groupby("mois")["pluie_mm"].mean(),
        }
    )
    comp["ecart_pluie_pct"] = (
        (comp[f"pluie_{label_b}"] - comp[f"pluie_{label_a}"]) / comp[f"pluie_{label_a}"] * 100
    )
    comp.index = MOIS
    comp.index.name = "mois"
    return comp.round(1), label_a, label_b


# Reperes de l'axe vertical : jour de l'annee -> date lisible
REPERES_DATES = {
    46: "15 févr.",
    60: "1er mars",
    74: "15 mars",
    91: "1er avril",
    105: "15 avril",
    121: "1er mai",
    135: "15 mai",
    152: "1er juin",
}


def plot_onsets(onsets: pd.DataFrame, name: str, out: Path):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(onsets.index, onsets["debut_imerg_jour"], marker="o", color="#1F6F50", label="GPM IMERG")
    if "debut_power_jour" in onsets:
        ax.plot(onsets.index, onsets["debut_power_jour"], marker="o", color="#9DB4C0",
                linestyle="--", label="NASA POWER (biaisé)")
    jours = onsets.filter(like="_jour").astype(float).stack()
    reperes = {j: d for j, d in REPERES_DATES.items() if jours.min() - 10 <= j <= jours.max() + 10}
    ax.set_yticks(list(reperes), list(reperes.values()))
    ax.invert_yaxis()
    ax.set_ylabel("Début de la saison des pluies")
    ax.set_title(f"{name.title()} : date de début de la saison des pluies")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_decades(comp, label_a, label_b, name, out: Path):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(12)
    w = 0.4
    ax.bar([i - w / 2 for i in x], comp[f"pluie_{label_a}"], w, label=label_a, color="#9DB4C0")
    ax.bar([i + w / 2 for i in x], comp[f"pluie_{label_b}"], w, label=label_b, color="#1F6F50")
    ax.set_xticks(list(x), MOIS_ACCENTS)
    ax.set_ylabel("Pluie moyenne (mm/mois)")
    ax.set_title(f"{name.title()} : pluie mensuelle, {label_a} vs {label_b} (GPM IMERG)")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def day_to_date(day_of_year: float) -> str:
    if pd.isna(day_of_year):
        return "-"
    return (pd.Timestamp("2001-01-01") + pd.Timedelta(days=int(round(day_of_year)) - 1)).strftime("%d/%m")


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Pluie journaliere GPM IMERG : debut de saison et decennies")
    parser.add_argument("--lat", type=float, default=5.44)
    parser.add_argument("--lon", type=float, default=10.05)
    parser.add_argument("--start", type=int, default=2005)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--name", default="dschang")
    parser.add_argument("--box", type=float, default=0.15)
    parser.add_argument("--workers", type=int, default=4,
                        help="Nombre de requetes en parallele (monte a 8 si ta connexion le permet)")
    parser.add_argument("--mois-debut", type=int, default=2,
                        help="Premier mois lu chaque annee (le debut de saison se cherche a partir du 15 fevrier)")
    parser.add_argument("--mois-fin", type=int, default=6,
                        help="Dernier mois lu chaque annee")
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    cache_path = PROCESSED_DIR / f"{args.name}_imerg_journalier.csv"
    months = range(args.mois_debut, args.mois_fin + 1)
    rain = fetch_imerg_daily(args.lat, args.lon, args.start, args.end,
                             args.box, args.workers, months, cache_path)
    rain = rain[rain.index.month.isin(months)]

    all_days = pd.date_range(f"{args.start}-01-01", f"{args.end}-12-31")
    expected = int(all_days.month.isin(months).sum())
    if len(rain) < expected:
        print(f"\nAttention : {expected - len(rain)} jours manquants. "
              f"Relance le script pour les recuperer avant d'utiliser les resultats.")

    # Debut de saison avec IMERG (meme definition qu'a l'etape 1)
    onsets = rainy_season_onset(rain.to_frame("pluie_mm")).rename(
        columns={"debut_saison": "debut_imerg", "debut_saison_jour": "debut_imerg_jour"}
    )
    power_annual = PROCESSED_DIR / f"{args.name}_annuel.csv"
    if power_annual.exists():
        power = pd.read_csv(power_annual).set_index("annee")
        onsets["debut_power_jour"] = power["debut_saison_jour"]
    onsets.to_csv(PROCESSED_DIR / f"{args.name}_debut_saison_imerg.csv")

    # Comparaison des decennies : pluie IMERG MENSUELLE de l'etape 2 (annee complete)
    monthly_csv = PROCESSED_DIR / f"{args.name}_imerg_mensuel.csv"
    if not monthly_csv.exists():
        raise SystemExit(f"{monthly_csv} introuvable : lance d'abord scripts/imerg_dschang.py")
    imerg_monthly = pd.read_csv(monthly_csv, parse_dates=["date"]).set_index("date")["pluie_mm"]
    imerg_monthly = imerg_monthly[(imerg_monthly.index.year >= args.start)
                                  & (imerg_monthly.index.year <= args.end)]

    split = args.start + (args.end - args.start + 1) // 2
    comp, label_a, label_b = compare_decades(imerg_monthly, split)
    comp.to_csv(PROCESSED_DIR / f"{args.name}_imerg_comparaison_decennies.csv")

    plot_onsets(onsets, args.name, FIG_DIR / f"{args.name}_debut_saison_imerg.png")
    plot_decades(comp, label_a, label_b, args.name,
                 FIG_DIR / f"{args.name}_imerg_pluie_decennies.png")

    # Resume console
    j = onsets["debut_imerg_jour"].astype(float)
    ja = j[j.index < split]
    jb = j[j.index >= split]
    yearly = imerg_monthly.resample("YS").sum()
    print("\n===== RESUME (GPM IMERG journalier) =====")
    print(f"Jours lus : {len(rain)} / {expected} (mois {args.mois_debut} a {args.mois_fin})")
    print(f"Pluie annuelle moyenne : {yearly[yearly.index.year < split].mean():.0f} mm ({label_a}) "
          f"-> {yearly[yearly.index.year >= split].mean():.0f} mm ({label_b})")
    print(f"Debut des pluies, moyenne : {day_to_date(ja.mean())} ({label_a}) "
          f"-> {day_to_date(jb.mean())} ({label_b})")
    first, last = j.idxmin(), j.idxmax()
    print(f"Debut des pluies, plus precoce : {pd.Timestamp(onsets.loc[first, 'debut_imerg']):%d/%m/%Y} ; "
          f"plus tardif : {pd.Timestamp(onsets.loc[last, 'debut_imerg']):%d/%m/%Y} ; "
          f"ecart : {j.max() - j.min():.0f} jours")
    print("\nDebut de saison par annee :")
    print(onsets[["debut_imerg"]].to_string())
    print("\nEcart de pluie par mois (%) :")
    print(comp["ecart_pluie_pct"].to_string())
    print(f"\nCSV : {PROCESSED_DIR}")
    print(f"Graphiques : {FIG_DIR}")


if __name__ == "__main__":
    main()