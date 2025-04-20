import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlmodel import select
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.api.deps import SessionDep, StorageDep
from app.schemas.read import EtudiantFullRead
from app.models import Etudiant, Candidature, Campus, Campagne
from app.schemas.enums import Note, CampagneStatus

router = APIRouter(prefix="/candidature", tags=["candidature"])


class CandidatureCoursRequestItem(BaseModel):
    sigle: str
    titre: str = ""
    note: Note = Note.non_specifie


@router.post("/", response_model=EtudiantFullRead)
async def create_candidature(
    session: SessionDep,
    storage: StorageDep,
    code_permanent: str = Form(...),
    nom: str = Form(...),
    prenom: str = Form(...),
    cycle: int = Form(...),
    trimestre: int = Form(...),
    campus: str = Form(""),
    programme: str = Form(""),
    email: str = Form(""),
    courses_json: str = Form(
        "[]", description="JSON string representation of the courses list"
    ),
    resume: UploadFile = File(None, description="Student's resume file (e.g., PDF)"),
):
    campagne = session.exec(
        select(Campagne).where((Campagne.trimestre == trimestre) & (Campagne.status == CampagneStatus.en_cours))
    ).first()

    if not campagne:
        raise HTTPException(
            status_code=400,
            detail=f"Trimestre invalid {trimestre}. Aucun trimestre en cours de disponible.",
        )

    try:
        courses_data = TypeAdapter(List[CandidatureCoursRequestItem]).validate_json(
            courses_json
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format for courses: {e}",
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Courses field is not valid JSON.",
        )

    existing_student = session.exec(
        select(Etudiant).where(
            ((Etudiant.code_permanent == code_permanent) | (Etudiant.email == email))
            & (Etudiant.trimestre == trimestre)
        )
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Une candidature existe déjà pour cet étudiant dans ce trimestre.",
        )

    new_student = Etudiant(
        code_permanent=code_permanent,
        email=email,
        nom=nom,
        prenom=prenom,
        cycle=cycle,
        campus=Campus(campus) if campus else Campus.non_specifie,
        programme=programme,
        trimestre=trimestre,
    )
    session.add(new_student)
    session.commit()
    session.refresh(new_student)

    assert new_student.id is not None, "Student ID should not be None after commit."

    for course in courses_data:
        try:
            candidature = Candidature(
                id_etudiant=new_student.id,
                sigle=course.sigle,
                titre=course.titre,
                trimestre=trimestre,
                note=course.note,
            )
            session.add(candidature)
        except KeyError as e:
            session.rollback()

    session.commit()

    if resume:
        try:
            storage.save_file(new_student.get_file_name, resume)
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save resume file: {e}. Student creation rolled back.",
            )
        finally:
            await resume.close()

    session.refresh(new_student)
    return new_student


@router.get("/{trimestre}/{student_id}/resume", response_class=FileResponse)
async def download_candidature_resume(
    student_id: int,
    trimestre: int,
    session: SessionDep,
    storage: StorageDep,
):
    student = session.exec(
        select(Etudiant).where(
            Etudiant.id == student_id, Etudiant.trimestre == trimestre
        )
    ).first()

    assert student, f"No student found with ID {student_id} for trimester {trimestre}."

    try:
        return storage.read_file(student.get_file_name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Resume file not found for student {student_id}, trimester {trimestre}.",
        )


@router.get("/", response_model=list[EtudiantFullRead])
def get_candidatures(trimestre: int, session: SessionDep):
    return session.exec(select(Etudiant).where(Etudiant.trimestre == trimestre)).all()


@router.put("/{student_id}", response_model=EtudiantFullRead)
async def update_student(
    student_id: int,
    session: SessionDep,
    storage: StorageDep,
    trimestre: int = Form(None),
    code_permanent: Optional[str] = Form(None),
    nom: Optional[str] = Form(None),
    prenom: Optional[str] = Form(None),
    cycle: Optional[int] = Form(None),
    campus: Optional[str] = Form(""),
    programme: Optional[str] = Form(""),
    email: Optional[str] = Form(""),
    courses_json: Optional[str] = Form(
        None, description="JSON string representation of the courses list"
    ),
    resume: Optional[UploadFile] = File(
        None, description="Student's resume file (e.g., PDF)"
    ),
):
    student = session.get(Etudiant, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if nom:
        student.nom = nom
    if prenom:
        student.prenom = prenom
    if cycle:
        student.cycle = cycle
    if email:
        student.email = email
    if campus:
        try:
            student.campus = Campus(campus)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campus value")
    if programme:
        student.programme = programme
    if trimestre:
        student.trimestre = trimestre

    session.add(student)
    session.commit()

    assert student.id is not None, "Student ID should not be None after commit."

    if courses_json is not None:
        try:
            courses_data = TypeAdapter(List[CandidatureCoursRequestItem]).validate_json(
                courses_json
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON format for courses: {e}",
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Courses field is not valid JSON.",
            )

        existing_candidatures = session.exec(
            select(Candidature).where(Candidature.id_etudiant == student.id)
        ).all()

        existing_sigles = {c.sigle for c in existing_candidatures}
        new_sigles = {course.sigle for course in courses_data}
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        for course in existing_candidatures:
            if course.sigle in sigles_to_remove:
                session.delete(course)
            else:
                course.note = [c for c in courses_data if c.sigle == course.sigle][
                    0
                ].note

        processed_cours = set()
        for cours in courses_data:
            if cours.sigle in processed_cours:
                continue
            if cours.sigle in sigles_to_add:
                try:
                    candidature = Candidature(
                        id_etudiant=student.id,
                        sigle=cours.sigle,
                        titre=cours.titre,
                        trimestre=trimestre,
                        note=cours.note,
                    )
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid Note value")

                session.add(candidature)
        session.commit()

    if resume:
        try:
            storage.save_file(student.get_file_name, resume)
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save resume file: {e}. Student creation rolled back.",
            )
        finally:
            await resume.close()

    session.refresh(student, attribute_names=["candidature"])

    return student


@router.delete("/{student_id}")
def delete_student(student_id: int, session: SessionDep, storage: StorageDep):
    student = session.get(Etudiant, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    storage.delete_file(student.get_file_name)
    session.delete(student)
    session.commit()

    return {"message": "Student and associated candidatures deleted successfully."}
