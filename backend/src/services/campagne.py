from datetime import datetime
from typing import Any

from structlog import BoundLogger
from sqlmodel import select
from sqlmodel import Session

from src.schemas import Campagne, Cours, Activite, Etudiant
from src.models.requests import CampagneCreateRequest, CampagneUpdateRequest
from src.models.uqo import CampagneConfig, ActiviteType, CampagneStatus

from src.exceptions import CampagneTooAhead


class CampagneService:
    def __init__(self, *, session: Session, logger: BoundLogger) -> None:
        self._session = session
        self._logger = logger

    def get_campagne(self, trimestre: int) -> Campagne | None:
        campagne = self._session.exec(
            select(Campagne).where(Campagne.trimestre == trimestre)
        ).first()
        return campagne

    async def add_campagne(self, payload: CampagneCreateRequest):
        def is_more_than_3_trimestres_ahead(target_trimestre: int) -> bool:
            now = datetime.now()
            current_trimestre = now.year * 10 + (
                1 if now.month <= 6 else 2 if now.month <= 9 else 3
            )
            to_index = lambda t: (t // 10) * 3 + (t % 10)
            return to_index(target_trimestre) - to_index(current_trimestre) > 3

        if is_more_than_3_trimestres_ahead(payload.trimestre):
            raise CampagneTooAhead

        # Create the Campagne
        campagne = Campagne(
            trimestre=payload.trimestre,
            config=CampagneConfig(**payload.config).model_dump(),
        )
        self._session.add(campagne)
        self._session.commit()
        self._session.refresh(campagne)

        processed_cours = set()
        for cours in payload.cours:
            if cours.sigle in processed_cours:
                continue
            cours = Cours(
                campagne=campagne,
                trimestre=payload.trimestre,
                sigle=cours.sigle,
                titre=cours.titre,
            )
            processed_cours.add(cours.sigle)
            self._session.add(cours)

        self._session.commit()

        self._session.refresh(campagne, attribute_names=["cours"])

        return campagne

    async def get_campagne_list(self):
        campagnes = self._session.exec(select(Campagne)).all()

        result: list[dict[str, Any]] = []
        for campagne in campagnes:
            configs = CampagneConfig(**campagne.config)

            # Cout total
            cout_total = 0
            total_assistant_par_cycle: tuple[set[int], set[int], set[int]] = (
                set(),
                set(),
                set(),
            )

            for cours in campagne.cours:
                for seance in cours.seance:
                    etudiant_contracts_total: dict[int, float] = {}
                    etudiant_contracts_nbr_seance_weekly: dict[
                        int, dict[ActiviteType, int]
                    ] = {}
                    for activite in seance.activite:
                        for responsable in activite.responsable:
                            total_assistant_par_cycle[
                                responsable.etudiant.cycle - 1
                            ].add(responsable.id_etudiant)

                            if responsable.id_etudiant not in etudiant_contracts_total:
                                etudiant_contracts_total[responsable.id_etudiant] = 0
                                etudiant_contracts_nbr_seance_weekly[
                                    responsable.id_etudiant
                                ] = {ActiviteType.TD: 0, ActiviteType.TP: 0}
                            etudiant_contracts_nbr_seance_weekly[
                                responsable.id_etudiant
                            ][activite.type] += 1

                            hrs_prepa = configs.activite_heure[
                                activite.type
                            ].preparation
                            hrs_travail = configs.activite_heure[activite.type].travail

                            # Add Prépa time only once per n activity in a week
                            if (
                                etudiant_contracts_nbr_seance_weekly[
                                    responsable.id_etudiant
                                ][activite.type]
                                == 1
                            ):
                                hrs_prepa = configs.activite_heure[
                                    activite.type
                                ].preparation
                                etudiant_contracts_total[responsable.id_etudiant] += (
                                    activite.nombre_seance
                                    * hrs_prepa
                                    * configs.echelle_salariale[
                                        responsable.etudiant.cycle - 1
                                    ]
                                )

                            etudiant_contracts_total[responsable.id_etudiant] += (
                                activite.nombre_seance
                                * hrs_travail
                                * configs.echelle_salariale[
                                    responsable.etudiant.cycle - 1
                                ]
                            )

                    tot_seance = sum(etudiant_contracts_total.values())
                    cout_total += tot_seance

            # Distribution des sceances
            activite_td = self._session.exec(
                select(Activite).where(
                    (Activite.type == ActiviteType.TD)
                    & (Activite.trimestre == campagne.trimestre)
                )
            ).all()
            nbr_td_total = len([activite.nombre_seance for activite in activite_td])

            activite_tp = self._session.exec(
                select(Activite).where(
                    (Activite.type == ActiviteType.TP)
                    & (Activite.trimestre == campagne.trimestre)
                )
            ).all()
            nbr_tp_total = len([activite.nombre_seance for activite in activite_tp])

            # Distribution des candidats
            etudiant = self._session.exec(
                select(Etudiant.cycle).where(Etudiant.trimestre == campagne.trimestre)
            ).all()
            nbr_candidature_cycle1 = etudiant.count(1)
            nbr_candidature_cycle2 = etudiant.count(2)
            nbr_candidature_cycle3 = etudiant.count(3)

            campagne_dict = {
                "id": campagne.id,
                "trimestre": campagne.trimestre,
                "status": campagne.status,
                "config": campagne.config,
                "cours": campagne.cours,
                "stats": {
                    "cout_total": float(f"{cout_total:.2f}"),
                    "nb_cours": len(campagne.cours),
                    "nbr_td_total": nbr_td_total,
                    "nbr_tp_total": nbr_tp_total,
                    "nbr_candidature_cycle1": nbr_candidature_cycle1,
                    "nbr_candidature_cycle2": nbr_candidature_cycle2,
                    "nbr_candidature_cycle3": nbr_candidature_cycle3,
                    "nbr_assistant_cycle1": len(total_assistant_par_cycle[0]),
                    "nbr_assistant_cycle2": len(total_assistant_par_cycle[1]),
                    "nbr_assistant_cycle3": len(total_assistant_par_cycle[2]),
                },
            }
            result.append(campagne_dict)

        return result

    async def update_campagne(self, campagne: Campagne, payload: CampagneUpdateRequest):
        # Update Campagne fields
        if payload.config is not None:
            campagne.config = CampagneConfig(**payload.config).model_dump()
        if payload.status is not None:
            campagne.status = payload.status

        self._session.add(campagne)
        self._session.commit()
        self._session.refresh(campagne)

        if payload.cours is not None:
            existing_courses = campagne.cours
            existing_sigles = {c.sigle for c in existing_courses}

            new_sigles = {c.sigle for c in payload.cours}
            sigles_to_add = new_sigles - existing_sigles
            sigles_to_remove = existing_sigles - new_sigles

            for course in existing_courses:
                if course.sigle in sigles_to_remove:
                    self._session.delete(course)

            processed_cours = set()
            for cours in payload.cours:
                if cours.sigle in processed_cours:
                    continue
                if cours.sigle in sigles_to_add:
                    new_course = Cours(
                        campagne=campagne,
                        trimestre=campagne.trimestre,
                        sigle=cours.sigle,
                        titre=cours.titre,
                    )
                    self._session.add(new_course)

            self._session.commit()

            self._session.refresh(campagne, attribute_names=["cours"])

        return campagne
