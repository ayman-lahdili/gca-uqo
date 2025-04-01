import uuid
from typing import Any, List

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.models import Campagne, Cours, CampagneStatus

router = APIRouter(prefix="/campagne", tags=["items"])

class CampagneCreateRequest(BaseModel):
    trimestre: int
    echelle_salariale: List[float] | None = None
    sigles: List[str]

class CampagneUpdateRequest(BaseModel):
    echelle_salariale: List[float] | None = None
    status: str | None = None
    sigles: List[str] | None = None

@router.post("/")
def create_campagne(
    payload: CampagneCreateRequest,
    session: SessionDep,
) -> Any:
    # Create the Campagne
    campagne = Campagne(
        trimestre=payload.trimestre,
        echelle_salariale=payload.echelle_salariale or [18.85, 24.49, 26.48],
    )
    session.add(campagne)
    session.commit()
    session.refresh(campagne)

    # Ensure campagne.id is not None
    assert campagne.id is not None, "Campagne ID should not be None after commit."

    # Create related Cours
    for sigle in payload.sigles:
        cours = Cours(
            id_campagne=campagne.id,
            sigle=sigle,
            titre="",  # Default empty title, can be updated later
        )
        session.add(cours)

    session.commit()
    return {
        "id": campagne.id,
        "trimestre": campagne.trimestre,
        "status": campagne.status.value,
        "salaire": campagne.echelle_salariale, 
        "cours": payload.sigles
    }

@router.get("/")
def get_campagnes(session: SessionDep) -> Any:
    campagnes = session.exec(select(Campagne)).all()
    result = []
    for campagne in campagnes:
        courses = session.exec(select(Cours).where(Cours.id_campagne == campagne.id)).all()
        result.append({
            "id": campagne.id,
            "trimestre": campagne.trimestre,
            "status": campagne.status.value,
            "salaire": campagne.echelle_salariale,
            "cours": courses,
        })
    return result

@router.put("/{trimestre}")
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

    # Ensure campagne.id is not None
    assert campagne.id is not None, "Campagne ID should not be None after commit."

    # Update related Cours if sigles are provided
    if payload.sigles is not None:
        # Fetch existing courses for the campagne
        existing_courses = session.exec(select(Cours).where(Cours.id_campagne == campagne.id)).all()
        existing_sigles = {course.sigle for course in existing_courses}

        # Determine courses to add and remove
        new_sigles = set(payload.sigles)
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        # Remove courses no longer present
        for course in existing_courses:
            if course.sigle in sigles_to_remove:
                session.delete(course)

        # Add new courses
        for sigle in sigles_to_add:
            new_course = Cours(
                id_campagne=campagne.id,
                sigle=sigle,
                titre="",  # Default empty title, can be updated later
            )
            session.add(new_course)

        session.commit()

    # Fetch updated courses from the database
    updated_courses = session.exec(select(Cours).where(Cours.id_campagne == campagne.id)).all()

    return {
        "id": campagne.id,
        "trimestre": campagne.trimestre,
        "status": campagne.status.value,
        "salaire": campagne.echelle_salariale,
        "cours": updated_courses,
    }

