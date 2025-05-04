from typing import Any, List, Dict, Literal, Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.core.uqo import UQOProgramService
from src.schemas.enums import Departement, Cycle
from src.schemas.uqo import UQOCours, UQOProgramme
from src.services.uqo_cours import UQOCoursService

router = APIRouter(tags=["uqo"])


@router.get("/v1/uqo/cours")
async def get_courses(
    *,
    uqo_service: Annotated[UQOCoursService, Depends(UQOCoursService.get_service)],
    departement: Departement, 
) -> List[UQOCours]:
    return uqo_service.get_courses(departement=departement)


@router.get("/v1/uqo/programmes", response_model=List[UQOProgramme])
def get_programmes(
    departement: Departement, 
    cycle: Cycle
):
    """
    Fetch the list of courses for a given department and cycle.
    """
    uqo_service = UQOProgramService()
    return uqo_service.get_programmes(departement=departement, cycle=cycle)
