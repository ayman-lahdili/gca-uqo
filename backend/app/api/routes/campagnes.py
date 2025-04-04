import uuid
from typing import Any, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from sqlalchemy import join 
from pydantic import BaseModel

from app.api.deps import SessionDep, HoraireDep
from app.models import Campagne, Cours, CampagneStatus, Seance, Activite
from app.base_models import ActiviteModel, SeanceModel, CoursModel, CampagneModel

router = APIRouter(prefix="/campagne", tags=["campagne"])

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

    assert campagne.id is not None, "Campagne ID should not be None"

    # Create related Cours
    for sigle in set(payload.sigles):
        cours = Cours(
            id_campagne=campagne.id,
            sigle=sigle,
            titre="",
        )
        session.add(cours)

    session.commit()

    return get_full_campagne(campagne.trimestre, session)

def get_campagne_iterator(trimestre: int, session: SessionDep) -> Sequence[Tuple[Campagne, Cours, Seance, Activite]]:
    q = session.exec(select(Campagne, Cours, Seance, Activite)
        .select_from(Campagne)
        .where(Campagne.trimestre == trimestre)
        .join(Cours, isouter=True)
        .join(Seance, isouter=True)
        .join(Activite, isouter=True)
    ).all()
    
    # Process all rows
    return q

def get_full_campagne(trimestre: int, session: SessionDep):
    q = get_campagne_iterator(trimestre, session)
    
    first_campagne = q[0][0]
    
    assert first_campagne.id is not None, "Campagne ID should not be None"

    result = CampagneModel(
        id=first_campagne.id,
        trimestre=first_campagne.trimestre,
        status=first_campagne.status.value,
        echelle_salariale=first_campagne.echelle_salariale,
        cours=[],
        model=first_campagne
    )
    
    # Process all rows
    for _, cours, seance, activite in q:
        if cours is None:
            continue

        assert cours.id is not None, "Cours ID should not be None"

        # Process cours if not already added
        cours_model = CoursModel(
            id=cours.id,
            sigle=cours.sigle,
            titre=cours.titre,
            status=cours.status.value,
            seance=[],
            cycle=cours.cycle,
            model=cours
        )

        print(cours_model.model)
        result.cours.append(cours_model) if cours_model not in result.cours else None
        
        if seance is None:
            continue
        
        assert seance.id is not None, "Seance ID should not be None"

        # Process seance if not already added to this cours
        seance_model = SeanceModel(
            id=seance.id,
            campus=seance.campus.value,
            activite=[],
            model=seance
        )
        cours_model.seance.append(seance_model) if seance_model not in cours_model.seance else None
        
        if activite is None:
            continue
        
        assert activite.id is not None, "Activite ID should not be None"

        # Add activite to its seance
        activite_model = ActiviteModel(
            id=activite.id,
            type=activite.type.value if activite.type else None,
            mode=activite.mode.value if activite.mode else None,
            jour=activite.jour,
            hr_debut=activite.hr_debut,
            hr_fin=activite.hr_fin,
            model=activite
        )
        seance_model.activite.append(activite_model) if activite_model not in seance_model.activite else None
    
    return result

@router.get("/")
def get_campagnes(session: SessionDep, trimestre: Optional[int] = None) -> Any:
    if trimestre:
        campagne = session.exec(select(Campagne).where(Campagne.trimestre == trimestre)).first()
        if not campagne:
            raise HTTPException(status_code=404, detail="Campagne not found")
        
        result = get_full_campagne(campagne.trimestre, session)

        return result
    else:
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

        assert campagne.id is not None, "Campagne ID should not be None"

        # Add new courses
        for sigle in sigles_to_add:
            new_course = Cours(
                id_campagne=campagne.id,
                sigle=sigle,
                titre="",
            )
            session.add(new_course)

        session.commit()

    return get_full_campagne(campagne.trimestre, session)

@router.post("/{trimestre}/sync")
def sync_campagne(
    trimestre: int,
    session: SessionDep,
    uqo_service: HoraireDep,
) -> Any:
    campagne = get_full_campagne(trimestre, session)
    
    if not campagne:
        raise HTTPException(status_code=404, detail="Campagne not found")

    for cours in campagne.cours:
        uqo_cours = uqo_service.get_course(cours.sigle)
        if not uqo_cours:
            continue

        cours_model = cours.model

        cours_model.titre = uqo_cours.titre

    session.commit()

    return get_full_campagne(campagne.trimestre, session)

        

        



    
