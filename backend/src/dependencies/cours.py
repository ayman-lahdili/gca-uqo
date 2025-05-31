from fastapi import Depends, Path, HTTPException

from typing import Annotated

from src.dependencies.context import Context
from src.schemas import Cours

async def get_current_course(
    *, trimestre: Annotated[int, Path()], sigle: Annotated[str, Path()], context: Context
) -> Cours:
    cours_service = context.factory.create_cours_service(trimestre)
    cours = await cours_service.get_course(sigle)

    if cours is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cours {sigle} introuvable pour le trimestre {trimestre}",
        )

    return cours


CurrentCourse = Annotated[Cours, Depends(get_current_course)]
