from fastapi import Depends, Path, HTTPException

from typing import Annotated

from src.dependencies.context import Context
from src.schemas import Activite

async def get_current_activite(
    *, trimestre: Annotated[int, Path()], activite_id: Annotated[int, Path()], context: Context
) -> Activite:
    groupe_service = context.factory.create_groupe_service(trimestre)
    activite = await groupe_service.get_activite(activite_id=activite_id)

    if activite is None:
        raise HTTPException(
            status_code=404,
            detail=f"Activité {activite_id} introuvable pour le trimestre {trimestre}",
        )

    return activite


CurrentActivite = Annotated[Activite, Depends(get_current_activite)]
