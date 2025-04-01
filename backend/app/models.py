from typing import Annotated, Optional

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