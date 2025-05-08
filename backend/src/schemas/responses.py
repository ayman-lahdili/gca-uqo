from sqlmodel import SQLModel
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from src.schemas.uqo import (
    ActiviteType,
    ActiviteMode,
    Campus,
    CoursStatus,
    CampagneStatus,
    Note,
    CampagneConfig,
    ActiviteStatus,
    ChangeType,
)


class EtudiantResponse(SQLModel):
    id: int
    code_permanent: str
    email: str
    nom: str
    prenom: str
    cycle: int
    campus: Campus
    programme: str
    trimestre: int


class EtudiantFullResponse(EtudiantResponse):
    candidature: list["CandidatureNoResponsableResponse"]


class ActiviteResponse(SQLModel):
    id: int
    type: ActiviteType | None = None
    mode: ActiviteMode | None = None
    status: ActiviteStatus | None = None
    jour: int
    hr_debut: int
    hr_fin: int
    date_debut: datetime
    date_fin: datetime
    change: Dict
    nombre_seance: int


class ActiviteFullResponse(ActiviteResponse):
    responsable: List["CandidatureResponse"]


class SeanceResponse(SQLModel):
    trimestre: int
    sigle: str
    groupe: str
    campus: List[Campus]
    activite: List[ActiviteFullResponse] = []
    change: Dict
    ressource: list[Dict[str, str | None]]


class CoursResponse(SQLModel):
    sigle: str
    trimestre: int
    titre: str
    status: CoursStatus
    cycle: int


class CandidatureResponse(SQLModel):
    id_etudiant: int
    note: Note
    sigle: str
    trimestre: int
    etudiant: EtudiantResponse
    titre: str


class CandidatureFullResponse(CandidatureResponse):
    activite: list[ActiviteFullResponse]


class CandidatureNoResponsableResponse(CandidatureResponse):
    activite: list[ActiviteResponse]


class CoursFullResponse(CoursResponse):
    seance: List[SeanceResponse] = []
    candidature: List[CandidatureResponse]
    change: Dict


class CampagneFullResponse(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    config: CampagneConfig
    cours: List[CoursFullResponse] = []


class CampagneResponse(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    config: CampagneConfig
    cours: List[CoursResponse] = []
    stats: Dict[str, float]


class ChangeInfo(BaseModel):
    change_type: ChangeType
    value: Dict[str, Any]


class ApprovalResponse(BaseModel):
    entity: Dict
    change: ChangeInfo
    approved: bool


class Message(BaseModel):
    message: str
