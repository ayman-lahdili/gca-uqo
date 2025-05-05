from typing import List

from fastapi import APIRouter

from src.schemas.uqo import UQOCours, UQOProgramme, Departement, Cycle
from src.dependencies.context import Context

router = APIRouter(tags=["uqo"])


@router.get("/v1/uqo/cours")
async def get_courses(
    *,
    departement: Departement,
    context: Context,
) -> List[UQOCours]:
    uqo_service = context.factory.create_uqo_course_service()
    return await uqo_service.get_courses(departement=departement)


@router.get("/v1/uqo/programmes", response_model=List[UQOProgramme])
def get_programmes(
    *,
    departement: Departement,
    cycle: Cycle,
    context: Context,
):
    uqo_service = context.factory.create_uqo_programme_service()
    return uqo_service.get_programmes(departement=departement, cycle=cycle)


@router.get("/v1/uqo/{trimestre}/horaire")
def get_horaire(
    *,
    trimestre: int,
    context: Context,
):
    uqo_service = context.factory.create_uqo_horaire_service(trimestre=trimestre)
    return uqo_service.get_horaire(trimestre=trimestre)
