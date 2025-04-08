import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.schemas.read import EtudiantFullRead
from app.models import Campagne, Cours, CampagneStatus, Etudiant, Candidature, Campus
from app.schemas.enums import Note

router = APIRouter(prefix="/candidature", tags=["candidature"])

class CandidatureCoursRequestItem(BaseModel):
    sigle: str
    titre: str = ""
    note: Note = Note.non_specifie

class CandidaturePayload(BaseModel):
    code_permanent: str
    nom: str
    prenom: str
    cycle: int
    trimestre: int
    campus: str = ""
    programme: str = ""
    email: str = ""
    courses: List[CandidatureCoursRequestItem] | None = None

@router.post("/", response_model=EtudiantFullRead)
def create_candidature(payload: CandidaturePayload, session: SessionDep):
    # Validate if the student already exists
    student = session.exec(
        select(Etudiant).where((Etudiant.code_permanent == payload.code_permanent) & (Etudiant.trimestre == payload.trimestre))
    ).first()

    if not student:
        # Create a new student if not found
        student = Etudiant(
            code_permanent=payload.code_permanent,
            email=payload.email,
            nom=payload.nom,
            prenom=payload.prenom,
            cycle=payload.cycle,
            campus=Campus(payload.campus) if payload.campus else Campus.non_specifie,
            programme=payload.programme,
            trimestre=payload.trimestre,
        )
        session.add(student)
        session.commit()
    else:
        print(student, student.code_permanent, student.trimestre, payload.trimestre, payload)

        raise HTTPException(
            status_code=400,
            detail="A candidature for this trimestre already exists for the student.",
        )

    assert student.id is not None, "Student ID should not be None after commit."

    # Process courses and create candidatures
    if payload.courses:
        for course in payload.courses:
            try:
                candidature = Candidature(
                    id_etudiant=student.id,
                    sigle=course.sigle,
                    titre=course.titre,
                    trimestre=payload.trimestre,
                    note=course.note,
                )
            except KeyError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {str(e)}",
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid note value")
            
            session.add(candidature)
        session.commit()

    session.refresh(student)
    return student

@router.get("/", response_model=list[EtudiantFullRead])
def get_candidatures(trimestre: int, session: SessionDep):
    students = session.exec(select(Etudiant).where(Etudiant.trimestre == trimestre)).all()

    return students

@router.put("/{student_id}", response_model=EtudiantFullRead)
def update_student(student_id: int, payload: CandidaturePayload, session: SessionDep):
    # Fetch the student by ID
    student = session.get(Etudiant, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    student.code_permanent = payload.code_permanent
    student.nom = payload.nom
    student.prenom = payload.prenom
    student.cycle = payload.cycle
    
    # Update student fields
    if payload.email:
        student.email = payload.email
    
    if payload.campus:
        try:
            student.campus = Campus(payload.campus)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campus value")
    
    if payload.programme:
        student.programme = payload.programme

    if payload.trimestre:
        student.trimestre = payload.trimestre

    assert student.id is not None, "Student ID should not be None after commit."

    session.add(student)
    session.commit()

    if payload.courses is not None:
        # Fetch existing candidatures for the student
        existing_candidatures = session.exec(
            select(Candidature).where(Candidature.id_etudiant == student.id)
        ).all()

        # Process courses and update candidatures
        existing_sigles = {c.sigle for c in existing_candidatures}
        new_sigles = {course.sigle for course in payload.courses}
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        # Add or update candidatures
        for course in existing_candidatures:
            if course.sigle in sigles_to_remove:
                session.delete(course)
            else:
                # Update note
                course.note = [c for c in payload.courses if c.sigle == course.sigle][0].note

        processed_cours = set()
        for cours in payload.courses:
            if cours.sigle in processed_cours:
                continue
            if cours.sigle in sigles_to_add:
                try:
                    # Add new candidature
                    candidature = Candidature(
                        id_etudiant=student.id,
                        sigle=cours.sigle,
                        titre=cours.titre,
                        trimestre=payload.trimestre,
                        note=cours.note,
                    )
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid Note value")
                
                session.add(candidature)
        session.commit()

    session.refresh(student, attribute_names=["candidature"])

    return student

@router.delete("/{student_id}")
def delete_student(student_id: int, session: SessionDep):
    # Fetch the student by ID
    student = session.get(Etudiant, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Delete the student
    session.delete(student)
    session.commit()

    return {"message": "Student and associated candidatures deleted successfully."}

