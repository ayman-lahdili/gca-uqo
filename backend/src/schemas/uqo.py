from pydantic import BaseModel
from typing import List

class UQOCours(BaseModel):
    sigle: str
    titre: str
    cycle: str
    credit: str
    préables: List[str] = []

class UQOProgramme(BaseModel):
    sigle: str
    label: str
    