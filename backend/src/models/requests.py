import json
from pydantic import BaseModel, ValidationError, TypeAdapter
from typing import List, Dict, Any
from fastapi import HTTPException, Form, UploadFile, File
from dataclasses import dataclass, field
from src.models.uqo import ActiviteStatus, Note, Campus, CampagneStatus


class CampagneCoursRequestItem(BaseModel):
    sigle: str
    titre: str = ""


class CampagneCreateRequest(BaseModel):
    trimestre: int
    config: Dict[str, Any] = {}
    cours: List[CampagneCoursRequestItem]


class CampagneUpdateRequest(BaseModel):
    config: Dict[str, Any] | None = None
    status: CampagneStatus | None = None
    cours: List[CampagneCoursRequestItem] | None = None


class ActiviteUpdateRequest(BaseModel):
    id: int
    candidature: List[int] | None = None
    nombre_seance: int | None = None
    status: ActiviteStatus | None = None


class SeanceUpdateRequest(BaseModel):
    activite: List[ActiviteUpdateRequest]


class CandidatureCoursItemRequest(BaseModel):
    sigle: str
    titre: str = ""
    note: Note = Note.non_specifie


class CandidaturePayload(BaseModel):
    code_permanent: str
    nom: str
    prenom: str
    cycle: int
    campus: str = ""
    programme: str = ""
    email: str = ""


@dataclass
class CandidatureForm:
    code_permanent: str = Form()
    nom: str = Form()
    prenom: str = Form()
    cycle: int = Form()
    campus: Campus = Form()
    programme: str = Form()
    email: str = Form()
    courses_json: str = Form(
        "[]", description="JSON string representation of the courses list"
    )
    resume: UploadFile = File(None, description="Student's resume file (e.g., PDF)")
    courses: List[CandidatureCoursItemRequest] = field(init=False)

    def __post_init__(self):
        try:
            self.courses = TypeAdapter(List[CandidatureCoursItemRequest]).validate_json(
                self.courses_json
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON format for courses: {e}",
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Courses field is not valid JSON.",
            )
