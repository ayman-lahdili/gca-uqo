import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.models import Campagne, Cours, CampagneStatus, Etudiant, Candidature, Campus
from app.schemas.enums import Note

router = APIRouter(prefix="/candidature", tags=["candidature"])

class CandidaturePayload(BaseModel):
    code_permanent: str
    nom: str
    prenom: str
    cycle: int
    trimestre: int
    campus: str = ""
    programme: str = ""
    email: str = ""
    courses: List[dict] | None = None  # Each dict contains 'sigle', 'titre', and 'score'

@router.post("/")
def create_candidature(payload: CandidaturePayload, session: SessionDep):
    # Validate if the student already exists
    student = session.exec(
        select(Etudiant).where(Etudiant.code_permanent == payload.code_permanent and Etudiant.trimestre == payload.trimestre)
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
        session.refresh(student)
    else:
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
                    sigle=course["sigle"],
                    trimestre=payload.trimestre,
                    note=Note(course.get("note")) if course.get("note") else Note.non_specifie,
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
    return {"message": "Candidature created successfully."}

@router.get("/")
def get_candidatures(trimestre: int, session: SessionDep):
    # Query students and their candidatures for the given trimestre
    students = session.exec(
        select(Etudiant).where(Etudiant.trimestre == trimestre)
    ).all()

    response = []
    for student in students:
        candidatures = session.exec(
            select(Candidature).where(Candidature.id_etudiant == student.id)
        ).all()

        response.append({
            "id": student.id,
            "email": student.email,
            "code_permanent": student.code_permanent,
            "nom": student.nom,
            "prenom": student.prenom,
            "campus": student.campus.value,
            "cycle": student.cycle,
            "programme": student.programme,
            "trimestre": student.trimestre,
            "candidature": [
                {
                    "id": candidature.id,
                    "note": candidature.note.value,
                    "sigle": candidature.sigle,
                }
                for candidature in candidatures
            ],
        })

    return response

@router.put("/{student_id}")
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

    if payload.courses is not None:
        # Fetch existing candidatures for the student
        existing_candidatures = session.exec(
            select(Candidature).where(Candidature.id_etudiant == student.id)
        ).all()

        # Process courses and update candidatures
        existing_sigles = {c.sigle for c in existing_candidatures}
        incoming_sigles = {course["sigle"] for course in payload.courses}

        # Add or update candidatures
        for course in payload.courses:
            if course["sigle"] in existing_sigles:
                # Update existing candidature
                candidature = next(c for c in existing_candidatures if c.sigle == course["sigle"])
                candidature.note = Note(course.get("note")) if course.get("note") else candidature.note
            else:
                try:
                    # Add new candidature
                    candidature = Candidature(
                        id_etudiant=student.id,
                        sigle=course["sigle"],
                        trimestre=payload.trimestre,
                        note=Note(course.get("note")),
                    )
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid Note value")
                
                session.add(candidature)

        # Remove candidatures that are not in the incoming list
        for candidature in existing_candidatures:
            if candidature.sigle not in incoming_sigles:
                session.delete(candidature)

    session.commit()
    return {"message": "Student and candidatures updated successfully."}

@router.delete("/{student_id}")
def delete_student(student_id: int, session: SessionDep):
    # Fetch the student by ID
    student = session.get(Etudiant, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Delete associated candidatures
    candidatures = session.exec(
        select(Candidature).where(Candidature.id_etudiant == student.id)
    ).all()
    for candidature in candidatures:
        session.delete(candidature)

    # Delete the student
    session.delete(student)
    session.commit()

    return {"message": "Student and associated candidatures deleted successfully."}

