from typing import Any, List

from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from src.dependencies.session import SessionDep
from src.dependencies.context import Context
from src.models import Campagne, Cours, Seance, Activite, Etudiant, Candidature
from src.schemas.uqo import (
    CoursStatus,
    ChangeType,
    CampagneConfig,
    ActiviteType,
    ActiviteStatus,
)
from src.schemas.responses import (
    CampagneFullResponse,
    CampagneResponse,
    CampagneStatus,
    SeanceResponse,
    CoursResponse,
    ChangeInfo,
    ApprovalResponse,
)
from src.schemas.requests import (
    CampagneCreateRequest,
    CampagneUpdateRequest,
    SeanceUpdateRequest,
)

from src.core.diffs import CoursDiffer

router = APIRouter(tags=["campagne"])


@router.post("/v1/campagne", response_model=CampagneFullResponse)
def create_campagne(
    payload: CampagneCreateRequest,
    session: SessionDep,
) -> Any:
    campagne = session.exec(
        select(Campagne).where(Campagne.trimestre == payload.trimestre)
    ).first()
    if campagne:
        raise HTTPException(
            status_code=404,
            detail=f"Campagne already exists for trimestre {payload.trimestre}",
        )

    # Cannot create a campagne in a trimestre more that 3 trimestres in the future
    def is_more_than_3_trimestres_ahead(target_trimestre: int) -> bool:
        now = datetime.now()
        current_trimestre = now.year * 10 + (
            1 if now.month <= 6 else 2 if now.month <= 9 else 3
        )
        to_index = lambda t: (t // 10) * 3 + (t % 10)
        return to_index(target_trimestre) - to_index(current_trimestre) > 3

    if is_more_than_3_trimestres_ahead(payload.trimestre):
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de créer une campagne pour le trimestre {payload.trimestre} car il est plus de 3 trimestres dans le futur.",
        )

    # Create the Campagne
    campagne = Campagne(
        trimestre=payload.trimestre,
        config=CampagneConfig(**payload.config).model_dump(),
    )
    session.add(campagne)
    session.commit()
    session.refresh(campagne)

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
        session.add(cours)

    session.commit()

    session.refresh(campagne, attribute_names=["cours"])

    return campagne


@router.get("/v1/campagne", response_model=List[CampagneResponse])
def get_campagnes(session: SessionDep) -> Any:
    campagnes = session.exec(select(Campagne)).all()

    result = []
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
                        total_assistant_par_cycle[responsable.etudiant.cycle - 1].add(
                            responsable.id_etudiant
                        )

                        if responsable.id_etudiant not in etudiant_contracts_total:
                            etudiant_contracts_total[responsable.id_etudiant] = 0
                            etudiant_contracts_nbr_seance_weekly[
                                responsable.id_etudiant
                            ] = {ActiviteType.TD: 0, ActiviteType.TP: 0}
                        etudiant_contracts_nbr_seance_weekly[responsable.id_etudiant][
                            activite.type
                        ] += 1

                        hrs_prepa = configs.activite_heure[activite.type].preparation
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
                            * configs.echelle_salariale[responsable.etudiant.cycle - 1]
                        )

                tot_seance = sum(etudiant_contracts_total.values())
                cout_total += tot_seance

        # Distribution des sceances
        activite_td = session.exec(
            select(Activite).where(
                (Activite.type == ActiviteType.TD)
                & (Activite.trimestre == campagne.trimestre)
            )
        ).all()
        nbr_td_total = len([activite.nombre_seance for activite in activite_td])

        activite_tp = session.exec(
            select(Activite).where(
                (Activite.type == ActiviteType.TP)
                & (Activite.trimestre == campagne.trimestre)
            )
        ).all()
        nbr_tp_total = len([activite.nombre_seance for activite in activite_tp])

        # Distribution des candidats
        etudiant = session.exec(
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
        result.append(CampagneResponse(**campagne_dict))

    return result


@router.get("/v1/campagne/{trimestre}", response_model=CampagneFullResponse)
def get_campagne_by_trimestre(
    trimestre: int,
    session: SessionDep,
) -> Any:
    campagne = session.exec(
        select(Campagne).where(Campagne.trimestre == trimestre)
    ).first()
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    return campagne


@router.get("/v1/campagne/{trimestre}/cours", response_model=List[CoursResponse])
def get_cours_by_trimestre(
    trimestre: int,
    session: SessionDep,
) -> Any:
    campagne = session.exec(
        select(Campagne).where(Campagne.trimestre == trimestre)
    ).first()
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    return campagne.cours


@router.put("/v1/campagne/{trimestre}", response_model=CampagneFullResponse)
def update_campagne(
    trimestre: int,
    payload: CampagneUpdateRequest,
    session: SessionDep,
) -> Any:
    # Fetch the Campagne
    campagne = session.exec(
        select(Campagne).where(Campagne.trimestre == trimestre)
    ).first()
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    # Update Campagne fields
    if payload.config is not None:
        campagne.config = CampagneConfig(**payload.config).model_dump()
    if payload.status is not None:
        try:
            campagne.status = CampagneStatus(payload.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    session.add(campagne)
    session.commit()
    session.refresh(campagne)

    if payload.cours is not None:
        existing_courses = campagne.cours
        existing_sigles = {c.sigle for c in existing_courses}

        new_sigles = {c.sigle for c in payload.cours}
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        for course in existing_courses:
            if course.sigle in sigles_to_remove:
                session.delete(course)

        processed_cours = set()
        for cours in payload.cours:
            if cours.sigle in processed_cours:
                continue
            if cours.sigle in sigles_to_add:
                new_course = Cours(
                    campagne=campagne,
                    trimestre=trimestre,
                    sigle=cours.sigle,
                    titre=cours.titre,
                )
                session.add(new_course)

        session.commit()

        session.refresh(campagne, attribute_names=["cours"])

    return campagne


@router.post("/v1/campagne/{trimestre}/sync", response_model=CampagneFullResponse)
def sync_campagne(
    trimestre: int,
    session: SessionDep,
    context: Context,
) -> Any:
    uqo_service = context.factory.create_uqo_horaire_service(trimestre=trimestre)
    campagne = session.exec(
        select(Campagne).where(Campagne.trimestre == trimestre)
    ).first()

    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    for old_cours in campagne.cours:
        new_cours = uqo_service.get_course(old_cours.sigle)

        if not new_cours:
            old_cours.status = CoursStatus.non_confirmee
            continue
        else:
            old_cours.status = CoursStatus.confirmee

        differ = CoursDiffer(old_cours, new_cours)

        old_cours = differ.compare()

        for seance in old_cours.seance:
            for act in seance.activite:
                session.add(act)

        session.add(old_cours)

    session.commit()

    session.refresh(campagne, attribute_names=["cours"])

    return campagne


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/changes/approve", response_model=ApprovalResponse
)
def approve_course(trimestre: int, sigle: str, session: SessionDep):
    cours = session.exec(
        select(Cours).where((Cours.trimestre == trimestre) & (Cours.sigle == sigle))
    ).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    approved_change = ChangeInfo(**cours.change)

    if approved_change.change_type == ChangeType.MODIFIED:
        for field, value in approved_change.value.items():
            setattr(cours, field, value["new"])

        cours.change["change_type"] = ChangeType.UNCHANGED
        cours.change["value"] = {}

        session.add(cours)

    session.commit()

    return ApprovalResponse(
        entity=cours.model_dump(), change=approved_change, approved=True
    )


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/{groupe}/changes/approve",
    response_model=ApprovalResponse,
)
def approve_seance(trimestre: int, sigle: str, groupe: str, session: SessionDep):
    seance = session.exec(
        select(Seance).where(
            Seance.trimestre == trimestre,
            Seance.sigle == sigle,
            Seance.groupe == groupe,
        )
    ).first()

    if not seance:
        raise HTTPException(status_code=404, detail="Seance not found")

    approved_change = ChangeInfo(**seance.change)

    if approved_change.change_type == ChangeType.MODIFIED:
        for field, value in approved_change.value.items():
            setattr(seance, field, value["new"])

        seance.change["change_type"] = ChangeType.UNCHANGED
        seance.change["value"] = {}

        session.add(seance)

    if approved_change.change_type == ChangeType.ADDED:
        seance.change["change_type"] = ChangeType.UNCHANGED
        seance.change["value"] = {}

    if approved_change.change_type == ChangeType.REMOVED:
        session.delete(seance)

    session.commit()

    return ApprovalResponse(
        entity=seance.model_dump(), change=approved_change, approved=True
    )


@router.patch(
    "/v1/campagne/{trimestre}/{sigle}/{groupe}/{activite_id}/changes/approve",
    response_model=SeanceResponse,
)
def approve_activite(
    trimestre: int, sigle: str, groupe: str, activite_id: int, session: SessionDep
):
    seance = session.exec(
        select(Seance).where(
            Seance.trimestre == trimestre,
            Seance.sigle == sigle,
            Seance.groupe == groupe,
        )
    ).first()

    if not seance:
        raise HTTPException(status_code=404, detail="Seance not found")

    activite = session.exec(select(Activite).where(Activite.id == activite_id)).first()

    if not activite:
        raise HTTPException(status_code=404, detail="Activite not found")

    approved_change = ChangeInfo(**activite.change)

    if approved_change.change_type == ChangeType.ADDED:
        activite.change["change_type"] = ChangeType.UNCHANGED
        activite.change["value"] = {}

    if approved_change.change_type == ChangeType.REMOVED:
        session.delete(activite)

    session.refresh(seance, attribute_names=["activite"])
    session.commit()

    return seance


@router.put("/v1/campagne/{trimestre}/{sigle}/{groupe}", response_model=SeanceResponse)
def modify_activity(
    trimestre: int,
    sigle: str,
    groupe: str,
    payload: SeanceUpdateRequest,
    session: SessionDep,
):
    seance = session.exec(
        select(Seance).where(
            Seance.trimestre == trimestre,
            Seance.sigle == sigle,
            Seance.groupe == groupe,
        )
    ).first()

    if not seance:
        raise HTTPException(status_code=404, detail="Seance not found")

    for act in payload.activite:
        print("act", act)
        activite = session.exec(select(Activite).where(Activite.id == act.id)).first()

        if not activite:
            raise HTTPException(status_code=404, detail="Activite not found")

        if act.candidature is not None:
            # Reset candidature
            activite.responsable = []
            session.add(activite)
            session.flush()

            # Assign new list from payload
            for candidature_id in act.candidature:
                print("actact.candidature:", act.candidature)
                candidature = session.exec(
                    select(Candidature).where(Candidature.id == candidature_id)
                ).first()

                if not candidature:
                    print("Candidature not found")
                    continue

                activite.responsable.append(candidature)

            session.add(activite)
        if act.nombre_seance:
            activite.nombre_seance = act.nombre_seance
            session.add(activite)
        if act.status:
            try:
                activite.status = ActiviteStatus(act.status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Status invalide")

        session.refresh(activite, attribute_names=["responsable"])
    session.refresh(seance, attribute_names=["activite"])
    session.commit()

    return seance
