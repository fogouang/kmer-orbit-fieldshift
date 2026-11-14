"""
Tests de l'API Field Shift (utilisent les donnees de data/processed/ pour la zone dschang).

Lancement (depuis la racine du projet) :
    uv run pytest backend/tests -q
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # dossier backend/

from app.main import app  # noqa: E402

client = TestClient(app)
API = "/api/v1"


def test_health():
    r = client.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cultures():
    r = client.get(f"{API}/cultures")
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert {"mais", "haricot", "arachide", "manioc", "pomme_de_terre"} <= ids


def test_zones_liste_dschang():
    r = client.get(f"{API}/zones")
    assert r.status_code == 200
    assert "dschang" in [z["nom"] for z in r.json()]


def test_climat():
    r = client.get(f"{API}/zones/dschang/climat")
    assert r.status_code == 200
    data = r.json()
    assert [s["saison"] for s in data["saisons"]] == ["saison_1", "saison_2"]
    assert len(data["pluie_mensuelle"]) == 12
    assert len(data["annees_reference"]) == 10


def test_sol():
    r = client.get(f"{API}/zones/dschang/sol")
    assert r.status_code == 200
    assert 3 < r.json()["ph"] < 9


def test_zone_inconnue():
    r = client.get(f"{API}/zones/inconnue/climat")
    assert r.status_code == 404


def test_rotations_par_defaut():
    r = client.post(f"{API}/rotations", json={})
    assert r.status_code == 200
    data = r.json()
    assert len(data["rotations"]) == 3
    notes = [x["note"] for x in data["rotations"]]
    assert notes == sorted(notes, reverse=True)
    # 3 compositions de cultures differentes
    compositions = {tuple(sorted(e["culture"] for e in x["sequence"])) for x in data["rotations"]}
    assert len(compositions) == 3
    # chaque rotation couvre exactement 4 saisons
    for x in data["rotations"]:
        assert sum(len(e["periodes"]) for e in x["sequence"]) == 4


def test_priorites_changent_le_classement():
    rendement = client.post(f"{API}/rotations", json={"priorites": {"rendement": 5, "eau": 1, "sol": 1}}).json()
    sol = client.post(f"{API}/rotations", json={"priorites": {"rendement": 1, "eau": 1, "sol": 5}}).json()
    assert rendement["rotations"][0]["sante_sol"] <= sol["rotations"][0]["sante_sol"]


def test_precedent_respecte_le_delai_de_retour():
    r = client.post(f"{API}/rotations", json={"precedent": "mais"})
    assert r.status_code == 200
    for x in r.json()["rotations"]:
        assert x["sequence"][0]["culture"] != "mais"


def test_precedent_inconnu():
    r = client.post(f"{API}/rotations", json={"precedent": "cafe"})
    assert r.status_code == 422


def test_analyse_de_sol_saisie():
    r = client.post(f"{API}/rotations", json={"sol": {"ph": 6.5, "argile_pct": 20}})
    assert r.status_code == 200
    sol = r.json()["sol_utilise"]
    assert sol["ph"] == 6.5 and sol["argile_pct"] == 20
    assert "agriculteur" in sol["source"]


def test_priorite_hors_limites():
    r = client.post(f"{API}/rotations", json={"priorites": {"rendement": 9}})
    assert r.status_code == 422


def test_successions_interdites_irad():
    # l'IRAD interdit le haricot juste apres l'arachide
    r = client.post("/api/v1/rotations", json={"zone": "dschang", "precedent": "arachide", "nb": 5})
    assert r.status_code == 200
    for rot in r.json()["rotations"]:
        assert rot["sequence"][0]["culture"] != "haricot"


def test_chaque_culture_une_seule_fois():
    # delai de retour IRAD de 3 a 4 ans : sur 2 ans, aucune culture ne revient
    r = client.post("/api/v1/rotations", json={"zone": "dschang", "nb": 5})
    for rot in r.json()["rotations"]:
        ids = [e["culture"] for e in rot["sequence"]]
        assert len(ids) == len(set(ids))


def test_conseils_et_normes():
    r = client.post("/api/v1/rotations", json={"zone": "dschang"})
    data = r.json()
    assert data["normes_irad"]["jachere"]
    assert all(rot["conseils"] for rot in data["rotations"])


def test_validation_station():
    r = client.get("/api/v1/zones/dschang/validation")
    assert r.status_code == 200
    assert "imerg" in r.json()["pluie_mensuelle"]

def test_rotations_en_anglais():
    r = client.post("/api/v1/rotations", json={"zone": "dschang", "langue": "en"})
    assert r.status_code == 200
    data = r.json()
    texte = " ".join(data["rotations"][0]["raisons"] + data["rotations"][0]["conseils"])
    assert "IRAD" in texte and "campagne" not in texte
    assert data["normes_irad"]["travail_du_sol"] == "Light tillage."
    noms = {e["nom"] for rot in data["rotations"] for e in rot["sequence"]}
    assert noms <= {"Maize", "Beans", "Groundnut", "Cassava", "Potato"}


def test_langue_inconnue_refusee():
    r = client.post("/api/v1/rotations", json={"zone": "dschang", "langue": "de"})
    assert r.status_code == 422
    


def test_rotation_actuelle_notee():
    # maïs et haricot qui reviennent chaque annee : notee, mais delai de retour IRAD signale
    r = client.post(f"{API}/rotations", json={"actuelle": ["mais", "haricot", "mais", "haricot"]})
    assert r.status_code == 200
    actuelle = r.json()["actuelle"]
    assert actuelle["rang"] == 0
    assert [e["culture"] for e in actuelle["sequence"]] == ["mais", "haricot", "mais", "haricot"]
    assert any("IRAD" in a for a in actuelle["regles_non_respectees"])
    assert r.json()["rotations"][0]["note"] >= actuelle["note"]


def test_rotation_actuelle_succession_interdite():
    r = client.post(f"{API}/rotations", json={"actuelle": ["mais", "mais", None, "haricot"], "langue": "en"})
    assert r.status_code == 200
    alertes = r.json()["actuelle"]["regles_non_respectees"]
    assert any("forbidden by IRAD" in a for a in alertes)


def test_rotation_actuelle_manioc_sur_deux_saisons():
    r = client.post(f"{API}/rotations", json={"actuelle": ["manioc", "manioc", "haricot", "mais"]})
    sequence = r.json()["actuelle"]["sequence"]
    assert sequence[0]["culture"] == "manioc" and len(sequence[0]["periodes"]) == 2


def test_rotation_actuelle_invalide():
    assert client.post(f"{API}/rotations", json={"actuelle": ["mais", "haricot"]}).status_code == 422
    assert client.post(f"{API}/rotations", json={"actuelle": ["cafe", None, None, None]}).status_code == 422
    assert client.post(f"{API}/rotations", json={"actuelle": [None, None, None, None]}).status_code == 422


def test_sans_rotation_actuelle():
    assert client.post(f"{API}/rotations", json={}).json()["actuelle"] is None