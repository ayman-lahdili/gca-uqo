from enum import Enum

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
    non_specifie = 'non-specife'

class ActiviteMode(str, Enum):
    PRESENTIEL = "PRESENTIEL"
    DISTANCIEL = "DISTANCIEL"

class ActiviteType(str, Enum):
    TD = "TD"
    TP = "TP"
    COURS = "COURS"

class Note(str, Enum):
    A_p = "A+"
    A = "A"
    A_m = "A-"
    B_p = "B+"
    B = "B"
    B_m = "B-"
    non_specifie = 'non-specife'