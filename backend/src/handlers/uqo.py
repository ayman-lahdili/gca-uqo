from typing import List

from fastapi import APIRouter

from src.schemas.uqo import UQOCours, UQOProgramme, Departement, Cycle
from src.services.uqo import UQOCoursService, UQOProgrammeService

router = APIRouter(tags=["uqo"])


@router.get("/v1/uqo/cours")
async def get_courses(
    *,
    departement: Departement, 
) -> List[UQOCours]:
    uqo_service = UQOCoursService()
    return uqo_service.get_courses(departement=departement)


@router.get("/v1/uqo/programmes", response_model=List[UQOProgramme])
def get_programmes(
    *,
    departement: Departement, 
    cycle: Cycle
):
    uqo_service = UQOProgrammeService()
    return uqo_service.get_programmes(departement=departement, cycle=cycle)
