from typing import Optional, Any, Dict

from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from app.schemas.enums import Note, ActiviteMode, ActiviteType, CoursStatus, CampagneStatus, Campus
from app.schemas.change import Change
from sqlalchemy.types import TypeDecorator, VARCHAR
import json

class ChangeType(TypeDecorator):
    """Custom SQLAlchemy type for Change model"""
    impl = VARCHAR
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, Change):
            return value.model_dump_json()  # Use model_dump_json() in Pydantic v2
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            print('FILIALAS', value)
            return Change.model_validate_json(value)
        except ValueError:
            return Change()

class Campagne(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trimestre: int = Field(index=True)
    status: CampagneStatus = Field(default=CampagneStatus.en_cours)
    echelle_salariale: list[float] | None = Field(default=[18.85, 24.49, 26.48], sa_column=Column(JSON))

    cours: list["Cours"] = Relationship(back_populates="campagne")

class Cours(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    sigle: str = Field(index=True)
    titre: str
    status: CoursStatus = Field(default=CoursStatus.non_confirmee)
    cycle: int = Field(default=1)
    change: Change = Field(default=Change(), sa_column=Column(ChangeType)) 

    seance: list["Seance"] = Relationship(back_populates="cours")

    id_campagne: int | None = Field(default=None, foreign_key="campagne.id")
    campagne: Campagne = Relationship(back_populates="cours")

class Seance(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    campus: Campus = Field(default=Campus.gat)
    groupe: str
    change: Change = Field(default=Change(), sa_column=Column(ChangeType)) 

    id_cours: int | None = Field(default=None, foreign_key="cours.id")
    cours: Cours = Relationship(back_populates="seance")

    activite: list["Activite"] = Relationship(back_populates="seance")

class Activite(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    type: ActiviteType = Field(default=None)
    mode: ActiviteMode = Field(default=None)
    jour: int
    hr_debut: int
    hr_fin: int
    change: Change = Field(default=Change(), sa_column=Column(ChangeType)) 

    id_seance: int | None = Field(default=None, foreign_key="seance.id")
    seance: Seance = Relationship(back_populates="activite")

class Etudiant(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    code_permanent: str = Field(index=True)
    email: str
    nom: str
    prenom: str
    cycle: int
    campus: Campus = Field(default=Campus.non_specifie)
    programme: str
    trimestre: int

class Candidature(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    id_etudiant: int = Field(foreign_key="etudiant.id")
    id_activite: Optional[int] = Field(foreign_key="activite.id", default=None)
    note: Note = Field(default=Note.non_specifie)
    sigle: str
    trimestre: int

