from typing import Optional, Any, Dict
from datetime import datetime

from sqlmodel import Field, SQLModel, Column, JSON, Relationship, DATETIME
from app.schemas.enums import Note, ActiviteMode, ActiviteType, CoursStatus, CampagneStatus, Campus, ChangeType
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import ForeignKeyConstraint

class Campagne(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trimestre: int = Field(index=True)
    status: CampagneStatus = Field(default=CampagneStatus.en_cours)
    echelle_salariale: list[float] | None = Field(default=[18.85, 24.49, 26.48], sa_column=Column(JSON))

    cours: list["Cours"] = Relationship(back_populates="campagne")

class Cours(SQLModel, table=True):
    sigle: str = Field(index=True, primary_key=True)
    trimestre: int = Field(index=True, primary_key=True)
    titre: str
    status: CoursStatus = Field(default=CoursStatus.non_confirmee)
    cycle: int = Field(default=1)
    change: Dict[str, Any] = Field(default={'change_type': ChangeType.UNCHANGED, 'value': {}}, sa_column=Column(MutableDict.as_mutable(JSON))) 

    seance: list["Seance"] = Relationship(back_populates="cours")
    candidature: list["Candidature"] = Relationship(back_populates="cours")

    id_campagne: int | None = Field(default=None, foreign_key="campagne.id")
    campagne: Campagne = Relationship(back_populates="cours")

class Seance(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ['trimestre', 'sigle'],
            ['cours.trimestre', 'cours.sigle'],
        ),
    )
    
    campus: list[Campus] = Field(default=Campus.gat, sa_column=Column(JSON))
    ressource: list[Dict[str, str | None]] = Field(default=[], sa_column=Column(MutableList.as_mutable(JSON)))

    change: Dict = Field(default={'change_type': ChangeType.UNCHANGED, 'value': {}}, sa_column=Column(MutableDict.as_mutable(JSON))) 

    trimestre: int = Field(primary_key=True)
    sigle: str = Field(primary_key=True)
    groupe: str = Field(primary_key=True)

    cours: Cours = Relationship(back_populates="seance")

    activite: list["Activite"] = Relationship(back_populates="seance")

class Activite(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ['trimestre', 'sigle', 'groupe'],
            ['seance.trimestre', 'seance.sigle', 'seance.groupe'],
        ),
    )

    trimestre: int
    sigle: str
    groupe: str

    id: Optional[int] | None = Field(default=None, primary_key=True)
    type: ActiviteType = Field(default=None)
    mode: ActiviteMode = Field(default=None)
    jour: int
    hr_debut: int
    hr_fin: int
    date_debut: datetime
    date_fin: datetime

    change: Dict = Field(default={'change_type': ChangeType.UNCHANGED, 'value': {}}, sa_column=Column(MutableDict.as_mutable(JSON))) 

    seance: Seance = Relationship(back_populates="activite")

    responsable: list["Candidature"] = Relationship(back_populates="activite")

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

    candidature: list["Candidature"] = Relationship(back_populates="etudiant")
    
class Candidature(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ['sigle', 'trimestre'],
            ['cours.sigle', 'cours.trimestre'],
        ),
    )

    id: Optional[int] | None = Field(default=None, primary_key=True)
    id_etudiant: int = Field(foreign_key="etudiant.id")
    id_activite: int | None = Field(default=None, foreign_key="activite.id")
    note: Note = Field(default=Note.non_specifie)

    cours: Cours = Relationship(back_populates="candidature")

    etudiant: Etudiant = Relationship(back_populates="candidature")
    activite: Activite = Relationship(back_populates="responsable")

    sigle: str
    trimestre: int

