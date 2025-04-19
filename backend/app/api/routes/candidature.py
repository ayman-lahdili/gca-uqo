import uuid
import shutil # Import shutil for file operations
import json # Import json for parsing courses string
from typing import Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form # Add File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlmodel import func, select
from pydantic import BaseModel, TypeAdapter, ValidationError # Import for parsing JSON string

from app.api.deps import SessionDep
from app.schemas.read import EtudiantFullRead
from app.models import Campagne, Cours, CampagneStatus, Etudiant, Candidature, Campus
from app.schemas.enums import Note

# --- Configuration ---
UPLOAD_DIRECTORY = Path("./uploaded_resumes") # Directory to store uploaded files
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True) # Create dir if it doesn't exist

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
async def create_candidature(
        session: SessionDep,
        # --- Student Data as Form Fields ---
        code_permanent: str = Form(...),
        nom: str = Form(...),
        prenom: str = Form(...),
        cycle: int = Form(...),
        trimestre: int = Form(...),
        campus: str = Form(""),
        programme: str = Form(""),
        email: str = Form(""),
        # --- Courses as JSON String in Form Field ---
        courses_json: str = Form("[]", description="JSON string representation of the courses list"),
        # --- Resume File ---
        resume: UploadFile = File(None, description="Student's resume file (e.g., PDF)")
    ): 
    # --- Parse Courses JSON ---
    try:
        # Use pydantic's parse_raw_as for validation against the model
        courses_data = TypeAdapter(List[CandidatureCoursRequestItem]).validate_json(courses_json)
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
    
    # Validate if the student already exists
    existing_student  = session.exec(
        select(Etudiant).where((Etudiant.code_permanent == code_permanent) & (Etudiant.trimestre == trimestre))
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="A candidature for this trimestre already exists for the student.",
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

    # --- Save the Uploaded Resume File ---
    if resume:
        try:
            # Create a unique filename using student ID and trimester
            file_extension = Path(resume.filename).suffix if resume.filename else ".unknown"
            # Sanitize filename components if necessary (basic example here)
            safe_student_id = str(new_student.id)
            safe_trimestre = str(trimestre)
            resume_filename = f"{safe_student_id}_{safe_trimestre}_resume{file_extension}"
            destination_path = UPLOAD_DIRECTORY / resume_filename

            with destination_path.open("wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)

        except Exception as e:
            # Important: If file saving fails after student creation, you might want
            # to roll back the student creation or implement a cleanup mechanism.
            # For simplicity, we just raise an error here.
            session.rollback() # Rollback student creation if file save fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save resume file: {e}. Student creation rolled back."
            )
        finally:
            await resume.close() # Always close the file stream

    # Process courses and create candidatures
    if courses_data:
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
                # Rollback if adding a candidature fails
                session.rollback()
                # TODO Attempt to remove the already saved file if something goes wrong here
            
        session.commit()

    session.refresh(new_student)
    return new_student

@router.get("/{trimestre}/{student_id}/resume", response_class=FileResponse)
async def download_candidature_resume(
    student_id: int,
    trimestre: int,
    session: SessionDep # Inject session to verify student existence (optional but good)
):
    """
    Downloads the resume file associated with a specific student ID and trimester.
    """
    # Optional: Verify the student actually exists for this trimester
    student = session.exec(
        select(Etudiant).where(Etudiant.id == student_id, Etudiant.trimestre == trimestre)
    ).first()
    if not student:
         raise HTTPException(
            status_code=404,
            detail=f"No student found with ID {student_id} for trimester {trimestre}."
        )

    # --- Find the resume file ---
    # Search for files matching the pattern: {student_id}_{trimestre}_resume.*
    file_pattern = f"{student_id}_{trimestre}_resume.*"
    found_files = list(UPLOAD_DIRECTORY.glob(file_pattern))

    if not found_files:
        raise HTTPException(
            status_code=404,
            detail=f"Resume file not found for student {student_id}, trimester {trimestre}."
        )

    if len(found_files) > 1:
        # This shouldn't happen with the chosen naming convention, but handle defensively
        print(f"Warning: Multiple resume files found for pattern {file_pattern}. Serving the first one: {found_files[0]}")

    resume_path = found_files[0]

    # --- Return the file using FileResponse ---
    # Suggest a filename for the download dialog (can use the stored name)
    # Use application/octet-stream for generic download, or try to guess MIME type
    return FileResponse(
        path=resume_path,
        filename=resume_path.name, # Suggests the stored filename for download
        media_type='application/octet-stream' # Force download
    )

@router.get("/", response_model=list[EtudiantFullRead])
def get_candidatures(trimestre: int, session: SessionDep):
    students = session.exec(select(Etudiant).where(Etudiant.trimestre == trimestre)).all()

    return students

@router.put("/{student_id}", response_model=EtudiantFullRead)
async def update_student(
        student_id: int, 
        session: SessionDep,
        trimestre: int = Form(None),
        code_permanent: Optional[str] = Form(None),
        nom: Optional[str] = Form(None),
        prenom: Optional[str] = Form(None),
        cycle: Optional[int] = Form(None),
        campus: Optional[str] = Form(""),
        programme: Optional[str] = Form(""),
        email: Optional[str] = Form(""),
        # --- Courses as JSON String in Form Field ---
        courses_json: Optional[str] = Form("[]", description="JSON string representation of the courses list"),
        # --- Resume File ---
        resume: Optional[UploadFile] = File(None, description="Student's resume file (e.g., PDF)")
    ):
    # Fetch the student by ID
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
            # Use pydantic's parse_raw_as for validation against the model
            courses_data = TypeAdapter(List[CandidatureCoursRequestItem]).validate_json(courses_json)
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

        # Fetch existing candidatures for the student
        existing_candidatures = session.exec(
            select(Candidature).where(Candidature.id_etudiant == student.id)
        ).all()

        # Process courses and update candidatures
        existing_sigles = {c.sigle for c in existing_candidatures}
        new_sigles = {course.sigle for course in courses_data}
        sigles_to_add = new_sigles - existing_sigles
        sigles_to_remove = existing_sigles - new_sigles

        # Add or update candidatures
        for course in existing_candidatures:
            if course.sigle in sigles_to_remove:
                session.delete(course)
            else:
                # Update note
                course.note = [c for c in courses_data if c.sigle == course.sigle][0].note

        processed_cours = set()
        for cours in courses_data:
            if cours.sigle in processed_cours:
                continue
            if cours.sigle in sigles_to_add:
                try:
                    # Add new candidature
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
        print('asdasd', resume.filename)
        try:
            # Create a unique filename using student ID and trimester
            file_extension = Path(resume.filename).suffix if resume.filename else ".unknown"
            # Sanitize filename components if necessary (basic example here)
            safe_student_id = str(student.id)
            safe_trimestre = str(trimestre)
            resume_filename = f"{safe_student_id}_{safe_trimestre}_resume{file_extension}"
            destination_path = UPLOAD_DIRECTORY / resume_filename

            with destination_path.open("wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)

        except Exception as e:
            # Important: If file saving fails after student creation, you might want
            # to roll back the student creation or implement a cleanup mechanism.
            # For simplicity, we just raise an error here.
            session.rollback() # Rollback student creation if file save fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save resume file: {e}. Student creation rolled back."
            )
        finally:
            await resume.close()

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

