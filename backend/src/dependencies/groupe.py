from fastapi import Depends, Path, HTTPException

from typing import Annotated

from src.dependencies.context import Context
from src.schemas import Seance

async def get_current_groupe(
    *, trimestre: Annotated[int, Path()], sigle: Annotated[str, Path()], groupe: Annotated[str, Path()], context: Context
) -> Seance:
    groupe_service = context.factory.create_groupe_service(trimestre)
    current_groupe = await groupe_service.get_groupe(sigle=sigle, groupe=groupe)

    if current_groupe is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cours {sigle} avec groupe {groupe} introuvable pour le trimestre {trimestre}",
        )

    return current_groupe


CurrentGroupe = Annotated[Seance, Depends(get_current_groupe)]
