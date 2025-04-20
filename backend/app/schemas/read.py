from sqlmodel import SQLModel
from typing import List, Dict
from datetime import datetime
from app.schemas.enums import (
    ActiviteType,
    ActiviteMode,
    Campus,
    CoursStatus,
    CampagneStatus,
    Note,
    CampagneConfig,
    ActiviteStatus,
)


class EtudiantRead(SQLModel):
    id: int
    code_permanent: str
    email: str
    nom: str
    prenom: str
    cycle: int
    campus: Campus
    programme: str
    trimestre: int


class EtudiantFullRead(EtudiantRead):
    candidature: list["CandidatureReadNoResponsable"]


class ActiviteRead(SQLModel):
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


class ActiviteFullRead(ActiviteRead):
    responsable: List["CandidatureRead"]


class SeanceRead(SQLModel):
    trimestre: int
    sigle: str
    groupe: str
    campus: List[Campus]
    activite: List[ActiviteFullRead] = []
    change: Dict
    ressource: list[Dict[str, str | None]]


class CoursRead(SQLModel):
    sigle: str
    trimestre: int
    titre: str
    status: CoursStatus
    cycle: int


class CandidatureRead(SQLModel):
    id_etudiant: int
    note: Note
    sigle: str
    trimestre: int
    etudiant: EtudiantRead
    titre: str


class CandidatureFullRead(CandidatureRead):
    activite: list[ActiviteFullRead]


class CandidatureReadNoResponsable(CandidatureRead):
    activite: list[ActiviteRead]


class CoursFullRead(CoursRead):
    seance: List[SeanceRead] = []
    candidature: List[CandidatureRead]
    change: Dict


class CampagneFullRead(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    config: CampagneConfig
    cours: List[CoursFullRead] = []


class CampagneRead(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    config: CampagneConfig
    cours: List[CoursRead] = []
    stats: Dict[str, float]
