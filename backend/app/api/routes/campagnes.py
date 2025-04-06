from typing import Any, List, Dict
from copy import deepcopy

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from pydantic import BaseModel

from app.api.deps import SessionDep, HoraireDep
from app.models import Campagne, Cours, Seance, Activite
from app.schemas.enums import CoursStatus, ChangeType
from app.schemas.read import CampagneFullRead, CampagneRead, CampagneStatus

from app.core.diffs import CoursDiffer

router = APIRouter(prefix="/campagne", tags=["campagne"])

class CampagneCreateRequest(BaseModel):
    trimestre: int
    echelle_salariale: List[float] | None = None
    sigles: List[str]

class CampagneUpdateRequest(BaseModel):
    echelle_salariale: List[float] | None = None
    status: str | None = None
    sigles: List[str] | None = None


class ChangeInfo(BaseModel):
    change_type: ChangeType
    value: Dict[str, Any]

class ApprovalResponse(BaseModel):
    id: int
    entity_type: str
    change: ChangeInfo
    approved: bool

@router.post("/", response_model=CampagneFullRead)
def create_campagne(
    payload: CampagneCreateRequest,
    session: SessionDep,
) -> Any:
    campagne = session.exec(select(Campagne).where(Campagne.trimestre == payload.trimestre)).first()
    if campagne:
        raise HTTPException(status_code=404, detail=f"Campagne already exists for trimestre {payload.trimestre}")

    # Create the Campagne
    campagne = Campagne(
        trimestre=payload.trimestre,
        echelle_salariale=payload.echelle_salariale or [18.85, 24.49, 26.48],
    )
    session.add(campagne)
    session.commit()
    session.refresh(campagne)

    for sigle in set(payload.sigles):
        cours = Cours(
            campagne=campagne,
            sigle=sigle,
            titre=""
        )
        session.add(cours)

    session.commit()

    session.refresh(campagne, attribute_names=['cours'])

    return campagne

@router.get("/", response_model=List[CampagneRead])
def get_campagnes(session: SessionDep) -> Any:
    campagnes = session.exec(select(Campagne)).all()

    return campagnes

@router.get("/{trimestre}", response_model=CampagneFullRead)
def get_campagne_by_trimestre(
    trimestre: int,
    session: SessionDep,
) -> Any:
    campagne = session.exec(select(Campagne).where(Campagne.trimestre == trimestre)).first()
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")
    
    return campagne

@router.put("/{trimestre}", response_model=CampagneFullRead)
def update_campagne(
    trimestre: int,
    payload: CampagneUpdateRequest,
    session: SessionDep,
) -> Any:
    # Fetch the Campagne
    campagne = session.exec(select(Campagne).where(Campagne.trimestre == trimestre)).first()
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    # Update Campagne fields
    if payload.echelle_salariale is not None:
        campagne.echelle_salariale = payload.echelle_salariale
    if payload.status is not None:
        try:
            campagne.status = CampagneStatus(payload.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    session.add(campagne)
    session.commit()
    session.refresh(campagne)

    if payload.sigles is not None:
        existing_courses = campagne.cours
        existing_sigles = {course.sigle for course in existing_courses}

        new_sigles = set(payload.sigles)
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        for course in existing_courses:
            if course.sigle in sigles_to_remove:
                session.delete(course)

        for sigle in sigles_to_add:
            new_course = Cours(
                campagne=campagne,
                sigle=sigle,
                titre="",
            )
            session.add(new_course)

        session.commit()

        session.refresh(campagne, attribute_names=['cours'])

    return campagne

@router.post("/{trimestre}/sync", response_model=CampagneFullRead)
def sync_campagne(
    trimestre: int,
    session: SessionDep,
    uqo_service: HoraireDep,
) -> Any:
    campagne = session.exec(select(Campagne).where(Campagne.trimestre == trimestre)).first()

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

        session.add(old_cours)
    
    session.commit()

    session.refresh(campagne, attribute_names=['cours'])

    return campagne

@router.patch('/cours/{cours_id}/changes/approve', response_model=ApprovalResponse)
def approve_course(cours_id: int, session: SessionDep):
    cours = session.exec(select(Cours).where(Cours.id == cours_id)).first()

    if not cours:
        raise HTTPException(status_code=404, detail="Cours not found")

    approved_change = ChangeInfo(**cours.change)

    if approved_change.change_type == ChangeType.MODIFIED:
        for field, value in approved_change.value.items():
            setattr(cours, field, value['new'])

        cours.change['change_type'] = ChangeType.UNCHANGED
        cours.change['value'] = {}

        session.add(cours)
    
    session.commit()
    
    assert cours.id

    return ApprovalResponse(
        id=cours.id,
        entity_type='cours',
        change=approved_change,
        approved=True
    )

@router.patch('/seance/{seance_id}/changes/approve', response_model=ApprovalResponse)
def approve_seance(seance_id: int, session: SessionDep):
    seance = session.exec(select(Seance).where(Seance.id == seance_id)).first()

    if not seance:
        raise HTTPException(status_code=404, detail="Seance not found")

    approved_change = ChangeInfo(**seance.change)

    if approved_change.change_type == ChangeType.MODIFIED:
        for field, value in approved_change.value.items():
            setattr(seance, field, value['new'])

        seance.change['change_type'] = ChangeType.UNCHANGED
        seance.change['value'] = {}

        session.add(seance)
    
    if approved_change.change_type == ChangeType.ADDED:
        seance.change['change_type'] = ChangeType.UNCHANGED
        seance.change['value'] = {}
    
    if approved_change.change_type == ChangeType.REMOVED:
        session.delete(seance)

    session.commit()
    
    assert seance.id

    return ApprovalResponse(
        id=seance.id,
        entity_type='cours',
        change=approved_change,
        approved=True
    )

@router.patch('/activite/{activite_id}/changes/approve', response_model=ApprovalResponse)
def approve_activite(activite_id: int, session: SessionDep):
    activite = session.exec(select(Activite).where(Activite.id == activite_id)).first()

    if not activite:
        raise HTTPException(status_code=404, detail="Activite not found")

    approved_change = ChangeInfo(**activite.change)
    
    if approved_change.change_type == ChangeType.ADDED:
        activite.change['change_type'] = ChangeType.UNCHANGED
        activite.change['value'] = {}
    
    if approved_change.change_type == ChangeType.REMOVED:
        session.delete(activite)

    session.commit()
    
    assert activite.id

    return ApprovalResponse(
        id=activite.id,
        entity_type='cours',
        change=approved_change,
        approved=True
    )

