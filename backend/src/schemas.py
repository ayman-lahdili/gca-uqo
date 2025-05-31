from typing import Optional, Any, Dict
from datetime import datetime

from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from src.models.uqo import (
    Note,
    ActiviteMode,
    ActiviteType,
    CoursStatus,
    CampagneStatus,
    ActiviteStatus,
    Campus,
    ChangeType,
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import ForeignKeyConstraint


class Campagne(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trimestre: int = Field(index=True)
    status: CampagneStatus = Field(default=CampagneStatus.en_cours)
    config: Dict[str, Any] = Field(
        default={}, sa_column=Column(MutableDict.as_mutable(JSON))
    )

    cours: list["Cours"] = Relationship(back_populates="campagne")


class Cours(SQLModel, table=True):
    sigle: str = Field(index=True, primary_key=True)
    trimestre: int = Field(index=True, primary_key=True)
    titre: str
    status: CoursStatus = Field(default=CoursStatus.non_confirmee)
    cycle: int = Field(default=1)
    change: Dict[str, Any] = Field(
        default={"change_type": ChangeType.UNCHANGED, "value": {}},
        sa_column=Column(MutableDict.as_mutable(JSON)),
    )

    seance: list["Seance"] = Relationship(back_populates="cours", cascade_delete=True)
    candidature: list["Candidature"] = Relationship(  # Forward ref needs quotes
        sa_relationship_kwargs=dict(
            primaryjoin="and_(Cours.sigle == Candidature.sigle, Cours.trimestre == Candidature.trimestre)",
            foreign_keys="[Candidature.sigle, Candidature.trimestre]",
            viewonly=True,
        )
    )

    id_campagne: int | None = Field(default=None, foreign_key="campagne.id")
    campagne: Campagne = Relationship(back_populates="cours")


class Seance(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["trimestre", "sigle"],
            ["cours.trimestre", "cours.sigle"],
        ),
    )

    campus: list[Campus] = Field(default=Campus.gat, sa_column=Column(JSON))
    ressource: list[Dict[str, str | None]] = Field(
        default=[], sa_column=Column(MutableList.as_mutable(JSON))
    )

    change: Dict = Field(
        default={"change_type": ChangeType.UNCHANGED, "value": {}},
        sa_column=Column(MutableDict.as_mutable(JSON)),
    )

    trimestre: int = Field(primary_key=True)
    sigle: str = Field(primary_key=True)
    groupe: str = Field(primary_key=True)

    cours: Cours = Relationship(back_populates="seance")

    activite: list["Activite"] = Relationship(
        back_populates="seance", cascade_delete=True
    )


class ActiviteCandidature(SQLModel, table=True):
    id_activite: int = Field(foreign_key="activite.id", primary_key=True)
    id_candidature: int = Field(foreign_key="candidature.id", primary_key=True)
    note: Note = Field(default=Note.non_specifie)


class Activite(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(
            ["trimestre", "sigle", "groupe"],
            ["seance.trimestre", "seance.sigle", "seance.groupe"],
        ),
    )

    trimestre: int
    sigle: str
    groupe: str

    id: Optional[int] | None = Field(default=None, primary_key=True)
    type: ActiviteType = Field(default=None)
    mode: ActiviteMode = Field(default=None)
    status: ActiviteStatus = Field(default=ActiviteStatus.non_confirmee)
    jour: int
    hr_debut: int
    hr_fin: int
    date_debut: datetime
    date_fin: datetime
    nombre_seance: int = 0

    change: Dict = Field(
        default={"change_type": ChangeType.UNCHANGED, "value": {}},
        sa_column=Column(MutableDict.as_mutable(JSON)),
    )

    seance: Seance = Relationship(back_populates="activite")

    responsable: list["Candidature"] = Relationship(
        back_populates="activite", link_model=ActiviteCandidature
    )


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

    candidature: list["Candidature"] = Relationship(
        back_populates="etudiant", cascade_delete=True
    )

    @property
    def get_file_name(self):
        return f"{self.trimestre}_{self.id}.pdf"


class Candidature(SQLModel, table=True):
    id: Optional[int] | None = Field(default=None, primary_key=True)
    id_etudiant: int = Field(foreign_key="etudiant.id")
    note: Note = Field(default=Note.non_specifie)

    etudiant: Etudiant = Relationship(back_populates="candidature")
    activite: list["Activite"] = Relationship(
        back_populates="responsable", link_model=ActiviteCandidature
    )
    sigle: str
    titre: str = ""
    trimestre: int
