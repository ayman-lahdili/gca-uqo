from enum import Enum
from pydantic import BaseModel
from typing import Literal, Dict


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class CampagneStatus(str, Enum):
    en_cours = "en_cours"
    cloturee = "cloturee"
    annulee = "annulee"


class CoursStatus(str, Enum):
    confirmee = "confirmee"
    non_confirmee = "non_confirmee"


class Campus(str, Enum):
    gat = "gatineau"
    stj = "st-jerome"
    non_specifie = "non-specife"


class ActiviteMode(str, Enum):
    PRESENTIEL = "PRES"
    DISTANCIEL = "NPRES"


class ActiviteType(str, Enum):
    TD = "Travaux dirigés"
    TP = "Travaux pratiques"
    COURS = "Cours régulier"


class ActiviteStatus(str, Enum):
    confirmee = "confirme"
    non_confirmee = "non_confirme"


class Note(str, Enum):
    A_p = "A+"
    A = "A"
    A_m = "A-"
    B_p = "B+"
    B = "B"
    B_m = "B-"
    non_specifie = "non-specife"


JourSemaine = Literal[
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]

Departement = Literal["DII", "INFOR"]


class ActiviteConfig(BaseModel):
    preparation: float
    travail: float


class CampagneConfig(BaseModel):
    echelle_salariale: list[float] = [18.85, 24.49, 26.48]
    activite_heure: Dict[ActiviteType, ActiviteConfig] = {
        ActiviteType.TD: ActiviteConfig(preparation=1, travail=2),
        ActiviteType.TP: ActiviteConfig(preparation=2, travail=3),
    }


if __name__ == "__main__":
    config = CampagneConfig().model_dump_json()
    print(config)
