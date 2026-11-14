from __future__ import annotations

from fastapi import APIRouter, Request

from app.modules.assistant.schemas import AssistantRequest, AssistantResponse
from app.modules.assistant.service import repondre

router = APIRouter(prefix="/assistant", tags=["Assistant"])


def adresse_ip(request: Request) -> str:
    # Derriere Nginx, l'adresse du visiteur arrive dans X-Real-IP ou X-Forwarded-For
    transmise = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for", "").split(",")[0]
    return transmise.strip() or (request.client.host if request.client else "inconnue")


@router.post(
    "",
    response_model=AssistantResponse,
    summary="Poser une question sur les rotations affichees",
    description=(
        "L'assistant (Claude) explique les rotations en langage simple. Il ne recoit que les donnees "
        "de Field Shift, recalculees par le serveur, et chaque chiffre de sa reponse est verifie."
    ),
)
def post_assistant(req: AssistantRequest, request: Request):
    return repondre(req, adresse_ip(request))