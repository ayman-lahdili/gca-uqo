from sqlmodel import SQLModel
from typing import List, Optional, Dict
from datetime import datetime
from app.schemas.enums import ActiviteType, ActiviteMode, Campus, CoursStatus, CampagneStatus, Note

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

class ActiviteRead(SQLModel):
    id: int
    type: ActiviteType | None = None
    mode: ActiviteMode | None = None
    jour: int
    hr_debut: int
    hr_fin: int
    date_debut: datetime
    date_fin: datetime
    change: Dict
    responsable: List[EtudiantRead]

class SeanceRead(SQLModel):
    trimestre: int
    sigle: str
    groupe: str
    campus: List[Campus]
    activite: List[ActiviteRead] = []
    change: Dict

class CoursRead(SQLModel):
    sigle: str
    trimestre: int
    titre: str
    status: CoursStatus
    cycle: int

class CandidatureRead(SQLModel):
    id_etudiant: int
    id_activite: Optional[int]
    note: Note
    sigle: str
    trimestre: int

class CoursFullRead(CoursRead):
    seance: List[SeanceRead] = []
    candidature: List[CandidatureRead]
    change: Dict

class CampagneFullRead(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    echelle_salariale: list[float] | None
    cours: List[CoursFullRead] = []

class CampagneRead(SQLModel):
    id: int
    trimestre: int
    status: CampagneStatus
    echelle_salariale: list[float] | None = None
    cours: List[CoursRead] = []
