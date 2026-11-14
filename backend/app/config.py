"""Configuration du backend Field Shift."""

from __future__ import annotations

import sys, os
from pathlib import Path


# Racine du projet kmer-orbit-fieldshift (backend/app/config.py -> 2 niveaux au-dessus)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CROPS_PATH = DATA_DIR / "crops.json"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Le moteur de rotation vit dans scripts/moteur_rotation.py (utilise aussi en ligne
# de commande). On le reutilise tel quel plutot que de dupliquer sa logique.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# Secrets (cle de l'assistant) : backend/.env, jamais dans git.
# En production, Docker les passe deja en variables d'environnement.
ENV_FILE = PROJECT_ROOT / "backend" / ".env"
if ENV_FILE.exists():
    for ligne in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))
            
# Origines autorisees a appeler l'API (frontend Nuxt en developpement)
# Origines autorisees a appeler l'API : le frontend Nuxt en local, quel que soit le port
CORS_ORIGIN_REGEX = r"http://(localhost|127\.0\.0\.1)(:\d+)?"

API_PREFIX = "/api/v1"