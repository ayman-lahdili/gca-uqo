from sqlmodel import SQLModel
from typing import List, Optional
from app.schemas.enums import ActiviteType, ActiviteMode, Campus, CoursStatus, CampagneStatus

class ActiviteRead(SQLModel):
    id: int
    type: ActiviteType | None = None
    mode: ActiviteMode | None = None
    jour: str
    hr_debut: str
    hr_fin: str

class SeanceRead(SQLModel):
    id: int
    campus: Campus
    groupe: str
    activite: List[ActiviteRead] = []

class CoursRead(SQLModel):
    id: int
    sigle: str
    titre: str
    status: CoursStatus
    cycle: int

class CoursFullRead(CoursRead):
    seance: List[SeanceRead] = []

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
