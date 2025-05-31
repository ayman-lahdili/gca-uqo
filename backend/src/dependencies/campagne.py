from fastapi import Depends, Path, HTTPException

from typing import Annotated

from src.dependencies.context import Context
from src.schemas import Campagne


def get_current_campagne(
    *, trimestre: Annotated[int, Path()], context: Context
) -> Campagne:
    campagne_service = context.factory.create_campagne_service()
    campagne = campagne_service.get_campagne(trimestre)

    if campagne is None:
        raise HTTPException(
            status_code=404,
            detail=f"Campagne introuvable pour le trimestre {trimestre}",
        )

    return campagne


CurrentCampagne = Annotated[Campagne, Depends(get_current_campagne)]
