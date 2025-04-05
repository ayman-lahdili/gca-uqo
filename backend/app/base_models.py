from pydantic import BaseModel, Field
from typing import List, Optional, Any
from app.models import Cours, Activite, Seance, Campagne

class ActiviteUQO(BaseModel):
    type: Optional[str] = None
    mode: Optional[str] = None
    jour: str
    hr_debut: str
    hr_fin: str

class ActiviteModel(BaseModel):
    id: int
    type: Optional[str] = None
    mode: Optional[str] = None
    jour: int
    hr_debut: int
    hr_fin: int
    model: Activite = Field(exclude=True)

class SeanceUQO(BaseModel):
    campus: str
    activite: List[ActiviteUQO] = []
    groupe: str

class SeanceModel(BaseModel):
    id: int
    campus: str
    activite: List[ActiviteModel] = []
    model: Seance = Field(exclude=True)

class CoursUQO(BaseModel):
    sigle: str
    titre: str
    cycle: int
    seance: List[SeanceUQO] = []

class CoursModel(BaseModel):
    id: int
    status: str
    sigle: str
    titre: str
    cycle: int
    seance: List[SeanceModel] = []
    model: Cours = Field(exclude=True)

class CampagneUQO(BaseModel):
    trimestre: int
    status: str
    echelle_salariale: List[float] | None = None
    cours: List[CoursUQO] = []

class CampagneModel(BaseModel):
    id: int
    trimestre: int
    status: str
    echelle_salariale: List[float] | None = None
    cours: List[CoursModel] = []
    model: Campagne = Field(exclude=True)
    