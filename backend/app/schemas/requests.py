from pydantic import BaseModel
from typing import List, Dict, Any
from app.schemas.enums import ActiviteStatus

class CampagneCoursRequestItem(BaseModel):
    sigle: str
    titre: str = ""


class CampagneCreateRequest(BaseModel):
    trimestre: int
    config: Dict[str, Any] = {}
    cours: List[CampagneCoursRequestItem]


class CampagneUpdateRequest(BaseModel):
    config: Dict[str, Any] | None = None
    status: str | None = None
    cours: List[CampagneCoursRequestItem] | None = None


class ActiviteUpdateRequest(BaseModel):
    id: int
    candidature: List[int] | None = None
    nombre_seance: int | None = None
    status: ActiviteStatus | None = None


class SeanceUpdateRequest(BaseModel):
    activite: List[ActiviteUpdateRequest]