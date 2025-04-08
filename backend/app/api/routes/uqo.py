from typing import Any, List, Dict

from fastapi import APIRouter

from app.api.deps import SessionDep, HoraireDep
from app.core.uqo import UQOCoursService
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
