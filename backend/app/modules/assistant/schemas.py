from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.modules.rotations.schemas import RotationRequest


class Message(BaseModel):
    role: Literal["user", "assistant"]
    contenu: str = Field(..., max_length=2000)


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    # Les memes choix que pour /rotations : le serveur recalcule lui-meme les resultats,
    # il ne fait jamais confiance a des resultats envoyes par le navigateur.
    contexte: RotationRequest = RotationRequest()
    historique: list[Message] = Field([], max_length=6)


class AssistantResponse(BaseModel):
    reponse: str
    verifiee: bool = Field(..., description="Tous les chiffres de la reponse existent dans les donnees Field Shift")
    modele: str