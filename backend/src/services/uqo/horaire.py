import requests
from datetime import datetime
import json
from typing import Dict, List, Any

from src.models import Cours, Seance, Activite
from src.schemas.uqo import ActiviteType, ActiviteMode, ChangeType, Campus, JourSemaine


class UQOHoraireService:
    def __init__(self, trimestre) -> None:
        self.url = "https://etudier.uqo.ca/activites/recherche-horaire-resultats-ajax"
        self.trimestre = trimestre
        self.horaire = self.get_horaire(self.trimestre)

    def get_horaire(self, trimestre: int):
        params = {
            "CdTrimestre": trimestre,
            "JourSem": [
                "dimanche",
                "lundi",
                "mardi",
                "mercredi",
                "jeudi",
                "vendredi",
                "samedi",
            ],
        }

        results = requests.get(self.url, params=params)
        # with open("tests/files/full_response.json", "r", encoding="utf-8") as f:
        #     return json.loads(f.read())

        return results.json()

    def get_course(self, sigle: str):
        # print(self.horaire)
        cours = None
        for cours_data in self.horaire:
            if cours_data["SigCrs"] == sigle:
                cours = self._parse_course(cours_data)

        return cours

    @staticmethod
    def _parse_course(cours: Dict[str, Any]) -> Cours:
        """Parse a course dictionary into a Cours object."""
        return Cours(
            sigle=cours["SigCrs"],
            trimestre=int(cours["CdTrimestreAct"]),
            titre=cours["TitreCrs"],
            cycle=int(cours["CdCyc"]),
            change={"change_type": ChangeType.UNCHANGED, "value": {}},
            seance=[
                Seance(
                    campus=_parse_campus(seance["LblRegrLieuEnsei"]),
                    trimestre=int(cours["CdTrimestreAct"]),
                    groupe=seance["Gr"],
                    change={"change_type": ChangeType.UNCHANGED, "value": {}},
                    sigle=cours["SigCrs"],
                    ressource=_parse_ressource(seance["LstEnsei"]),
                    activite=[
                        Activite(
                            trimestre=int(cours["CdTrimestreAct"]),
                            sigle=cours["SigCrs"],
                            groupe=seance["Gr"],
                            type=ActiviteType(activite["LblDescAct"]),
                            mode=ActiviteMode(activite["CdModeEnsei"]),
                            jour=_parse_jour(activite["JourSem"]),
                            hr_debut=int(activite["HrsDHor"]),
                            hr_fin=int(activite["HrsFHor"]),
                            date_debut=datetime.strptime(
                                activite["DateDHor"], "%Y-%m-%dT%H:%M:%S"
                            ),
                            date_fin=datetime.strptime(
                                activite["DateFHor"], "%Y-%m-%dT%H:%M:%S"
                            ),
                            change={"change_type": ChangeType.UNCHANGED, "value": {}},
                        )
                        for activite in seance["CollActCrsHor"]
                        if activite["LblDescAct"] != "Cours régulier"
                    ],
                )
                for seance in cours["LstActCrs"]
            ],
        )


def _parse_campus(unparsed: str) -> List[Campus]:
    unparsed = unparsed.strip().lower()
    campus = []
    if "gat" in unparsed:
        campus.append(Campus.gat)
    if "st" in unparsed:
        campus.append(Campus.stj)
    return campus


def _parse_jour(unparsed: JourSemaine):
    return {
        "lundi": 1,
        "mardi": 2,
        "mercredi": 3,
        "jeudi": 4,
        "vendredi": 5,
        "samedi": 6,
        "dimanche": 7,
    }[unparsed]


def _parse_ressource(unparsed: List[Dict[str, str]]):
    return [
        {
            "nom": prof.get("Nom"),
            "prenom": prof.get("Prenom"),
            "courriel": prof.get("AdrCourriel"),
        }
        for prof in unparsed
    ]
