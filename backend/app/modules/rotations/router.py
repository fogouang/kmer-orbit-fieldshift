from __future__ import annotations

from fastapi import APIRouter

from app.modules.rotations.schemas import RotationRequest, RotationResponse
from app.modules.rotations.service import proposer_rotations

router = APIRouter(prefix="/rotations", tags=["Rotations"])


@router.post(
    "",
    response_model=RotationResponse,
    summary="Proposer et comparer des rotations de cultures",
    description=(
        "Combine le climat (NASA GPM IMERG + NASA POWER), le sol (SoilGrids ou analyse "
        "de l'agriculteur), les caracteristiques des cultures et les priorites de "
        "l'agriculteur. Renvoie plusieurs rotations differentes, notees et expliquees."
    ),
)
def post_rotations(req: RotationRequest):
    return proposer_rotations(req)