from httpx import HTTPError, AsyncClient
from structlog import BoundLogger
from datetime import datetime
import json
from typing import Dict, List, Any

from sqlmodel import Session

from src.schemas import Cours, Seance, Activite, Campagne
from src.models.uqo import (
    ActiviteType,
    ActiviteMode,
    ChangeType,
    Campus,
    JourSemaine,
    CoursStatus,
)
from src.services.uqo.diffs import CoursDiffer

from src.cache import AsyncCache


class UQOHoraireService:
    def __init__(
        self,
        trimestre,
        *,
        diff_checker_cls: type[CoursDiffer] = CoursDiffer,
        horaire_cache: AsyncCache[List[dict[str, Any]]],
        session: Session,
        http_client: AsyncClient,
        logger: BoundLogger,
    ) -> None:
        self.url = "https://etudier.uqo.ca/activites/recherche-horaire-resultats-ajax"
        self.trimestre = trimestre
        self.horaire = None
        self.diff_checker_cls = diff_checker_cls
        self._horaire_cache = horaire_cache
        self._session = session
        self._http_client = http_client
        self._logger = logger

    async def get_horaire(self, trimestre: int):
        horaire_key = str(trimestre)

        return await self._horaire_cache.get_or_create(
            horaire_key, lambda: self._fetch_horaire(trimestre)
        )

    async def _fetch_horaire(self, trimestre: int):
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

        results = await self._http_client.get(self.url, params=params)
        # with open("tests/files/full_response.json", "r", encoding="utf-8") as f:
        #     return json.loads(f.read())

        return results.json()

    async def get_course(self, sigle: str):
        self.horaire = await self.get_horaire(self.trimestre)
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

    async def sync_courses(self, campagne: Campagne) -> Campagne:
        for old_course in campagne.cours:
            await self.sync_course(old_course)

        self._session.commit()
        self._session.refresh(campagne, attribute_names=["cours"])

        return campagne

    async def sync_course(self, old_cours: Cours) -> None:
        new_cours = await self.get_course(old_cours.sigle)

        if not new_cours:
            old_cours.status = CoursStatus.non_confirmee
            return
        else:
            old_cours.status = CoursStatus.confirmee

        differ = self.diff_checker_cls(old_cours, new_cours)

        old_cours = differ.compare()

        for seance in old_cours.seance:
            for act in seance.activite:
                self._session.add(act)

        self._session.add(old_cours)


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
