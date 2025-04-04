from typing import Annotated, Optional, Literal

from enum import Enum

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Column, JSON

class CampagneStatus(str, Enum):
    en_cours = "en_cours"
    cloturee = "cloturee"
    annulee = "annulee"

class Campagne(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trimestre: int = Field(index=True)
    status: CampagneStatus = Field(default=CampagneStatus.en_cours)
    echelle_salariale: list[float] | None = Field(default=[18.85, 24.49, 26.48], sa_column=Column(JSON))

class CoursStatus(str, Enum):
    confirmee = "confirmee"
    non_confirmee = "non_confirmee"

class Cours(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_campagne: int = Field(foreign_key="campagne.id")
    sigle: str = Field(index=True)
    titre: str
    status: CoursStatus = Field(default=CoursStatus.non_confirmee)
    cycle: int = Field(default=1)

class Campus(str, Enum):
    gat = "gatineau"
    stj = "st-jerome"
    non_specifie = 'non-specife'

class Seance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_cours: int = Field(foreign_key="cours.id")
    campus: Campus = Field(default=Campus.gat)
    groupe: str

class ActiviteType(str, Enum):
    TD = "TD"
    TP = "TP"
    COURS = "COURS"

class ActiviteMode(str, Enum):
    PRESENTIEL = "PRESENTIEL"
    DISTANCIEL = "DISTANCIEL"

class Activite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_seance: int = Field(foreign_key="seance.id")
    type: ActiviteType = Field(default=None)
    mode: ActiviteMode = Field(default=None)
    jour: int
    hr_debut: int
    hr_fin: int

class Etudiant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code_permanent: str = Field(index=True)
    email: str
    nom: str
    prenom: str
    cycle: int
    campus: Campus = Field(default=Campus.non_specifie)
    programme: str
    trimestre: int

class Note(str, Enum):
    A_p = "A+"
    A = "A"
    A_m = "A-"
    B_p = "B+"
    B = "B"
    B_m = "B-"
    non_specifie = 'non-specife'

class Candidature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_etudiant: int = Field(foreign_key="etudiant.id")
    id_activite: Optional[int] = Field(foreign_key="activite.id", default=None)
    note: Note = Field(default=Note.non_specifie)
    sigle: str
    trimestre: int

