from typing import Any, List, Dict

from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from pydantic import BaseModel

from app.api.deps import SessionDep, HoraireDep
from app.models import Campagne, Cours, Seance, Activite, Etudiant, Candidature
from app.schemas.enums import CoursStatus, ChangeType, CampagneConfig, ActiviteType
from app.schemas.read import CampagneFullRead, CampagneRead, CampagneStatus, ActiviteFullRead

from app.core.diffs import CoursDiffer

router = APIRouter(prefix="/campagne", tags=["campagne"])

class CampagneCoursRequestItem(BaseModel):
    sigle: str
    titre: str = ""

class CampagneCreateRequest(BaseModel):
    trimestre: int
    config: Dict[str, Any] = {}
    cours: List[CampagneCoursRequestItem]

class CampagneUpdateRequest(BaseModel):
    config: Dict[str, Any] | None = None
    status: str | None = None
    cours: List[CampagneCoursRequestItem] | None = None

class ChangeInfo(BaseModel):
    change_type: ChangeType
    value: Dict[str, Any]

class ApprovalResponse(BaseModel):
    entity: Dict
    change: ChangeInfo
    approved: bool

class ActiviteUpdateRequest(BaseModel):
    candidatures: List[str] = []
    nombre_seance: int | None = None

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
        config=CampagneConfig(**payload.config).model_dump()
        # echelle_salariale=payload.echelle_salariale or [18.85, 24.49, 26.48],
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
            titre=cours.titre
        )
        processed_cours.add(cours.sigle)
        session.add(cours)

    session.commit()

    session.refresh(campagne, attribute_names=['cours'])

    return campagne

@router.get("/", response_model=List[CampagneRead])
def get_campagnes(session: SessionDep) -> Any:
    campagnes = session.exec(select(Campagne)).all()

    result = []
    for campagne in campagnes:
        configs = CampagneConfig(**campagne.config)
        # Create a CampagneRead with computed stats

        # Cout total
        cout_total = 0
        total_assistant_par_cycle = [set(), set(), set()]

        campagne_candidatures = session.exec(select(Candidature).where(Candidature.trimestre == campagne.trimestre)).all()
        for candidature in campagne_candidatures:
            contrat = 0
            etudiants_set: set[str] = set()
            for activite in candidature.activite:
                if activite and activite.type != ActiviteType.COURS:
                    etudiant = candidature.etudiant
                    activite_heure = configs.activite_heure[activite.type]
                    taux_horaire = configs.echelle_salariale[etudiant.cycle-1]
                    temps_paye_par_seance = activite_heure.preparation + activite_heure.travail if etudiant.code_permanent in etudiants_set else activite_heure.travail
                    contrat = taux_horaire * temps_paye_par_seance * activite.nombre_seance
                    if etudiant.code_permanent not in etudiants_set:
                        total_assistant_par_cycle[etudiant.cycle-1].add(etudiant.code_permanent)
                    etudiants_set.add(etudiant.code_permanent)

                cout_total += contrat

        # Distribution des sceances
        activite_td = session.exec(select(Activite).where(Activite.type == ActiviteType.TD and Activite.trimestre == campagne.trimestre)).all()
        nbr_td_total = sum([activite.nombre_seance for activite in activite_td])

        activite_tp = session.exec(select(Activite).where(Activite.type == ActiviteType.TP and Activite.trimestre == campagne.trimestre)).all()
        nbr_tp_total = sum([activite.nombre_seance for activite in activite_tp])

        # Distribution des candidats
        etudiant = session.exec(select(Etudiant.cycle).where(Etudiant.trimestre == campagne.trimestre)).all()
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
                "cout_total": float(f'{cout_total:.2f}'),
                "nb_cours": len(campagne.cours),
                "nbr_td_total": nbr_td_total,
                "nbr_tp_total": nbr_tp_total,
                "nbr_candidature_cycle1": nbr_candidature_cycle1,
                "nbr_candidature_cycle2": nbr_candidature_cycle2,
                "nbr_candidature_cycle3": nbr_candidature_cycle3,
                "nbr_assistant_cycle1": len(total_assistant_par_cycle[0]),
                "nbr_assistant_cycle2": len(total_assistant_par_cycle[1]),
                "nbr_assistant_cycle3": len(total_assistant_par_cycle[2]),
            }
        }
        result.append(CampagneRead(**campagne_dict))
    
    return result

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

@router.patch('/{trimestre}/{sigle}/changes/approve', response_model=ApprovalResponse)
def approve_course(trimestre: int, sigle: str, session: SessionDep):
    cours = session.exec(select(Cours).where(Cours.trimestre == trimestre and Cours.sigle == sigle)).first()

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
    
    return ApprovalResponse(
        entity=cours.model_dump(),
        change=approved_change,
        approved=True
    )

@router.patch('/{trimestre}/{sigle}/{groupe}/changes/approve', response_model=ApprovalResponse)
def approve_seance(trimestre: int, sigle: str, groupe: str, session: SessionDep):
    seance = session.exec(select(Seance).where(Seance.trimestre == trimestre, Seance.sigle == sigle, Seance.groupe == groupe)).first()

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
    
    return ApprovalResponse(
        entity=seance.model_dump(),
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
    
    return ApprovalResponse(
        entity=activite.model_dump(),
        change=approved_change,
        approved=True
    )

@router.put('/activite/{activite_id}', response_model=ActiviteFullRead)
def modify_activity(payload: ActiviteUpdateRequest, activite_id, session: SessionDep):
    activite = session.exec(select(Activite).where(Activite.id == activite_id)).first()

    if not activite:
        raise HTTPException(status_code=404, detail="Activite not found")
    
    if payload.candidatures:
        # Reset candidature
        activite.responsable = []
        session.add(activite)
        session.flush()
        
        # Assign new list from payload
        for candidature_id in payload.candidatures:
            candidature = session.exec(select(Candidature).where(Candidature.id == candidature_id)).first()

            if not candidature:
                print('Candidature not found')
                continue
                
            activite.responsable.append(candidature)

            session.add(activite)
    if payload.nombre_seance:
        activite.nombre_seance = payload.nombre_seance
        session.add(activite)

    session.commit()
    session.refresh(activite, attribute_names=['responsable'])

    return activite
