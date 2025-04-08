from typing import Any, List, Dict, Literal

from fastapi import APIRouter

from app.api.deps import SessionDep, HoraireDep
from app.core.uqo import UQOCoursService, UQOProgramService
from app.schemas.enums import Departement

router = APIRouter(prefix="/uqo", tags=["uqo"])

@router.get("/cours", response_model=List[Dict[str, Any]])
def fetch_courses(departement: Departement, cycle: str = ""):
    """
    Fetch the list of courses for a given department and cycle.
    """
    uqo_service = UQOCoursService()
    courses = uqo_service.get_courses(departement=departement, cycle=cycle)
    return courses

@router.get("/programmes", response_model=List[Dict[str, Any]])
def fetch_programmes(departement: Departement, cycle: Literal["1", "2", "3"]):
    """
    Fetch the list of courses for a given department and cycle.
    """
    uqo_service = UQOProgramService()
    courses = uqo_service.get_programmes(departement=departement, cycle=cycle)
    unique = dict((obj["CdPrgAdm"], obj) for obj in courses).values()

    front = [{
        "sigle": c["CdPrgAdm"],
        "label": c["CdPrgAdm"] + " - " + c["LblPrg"]
    } for c in unique]

    return front