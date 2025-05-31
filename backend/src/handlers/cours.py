from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.dependencies.cours import CurrentCourse
from src.dependencies.context import Context

from src.models.responses import CoursFullResponse
from src.models.requests import CandidaturePayload

from src.exceptions import CandidatureExistsError, NoStudentsFoundError

router = APIRouter(tags=["cours"])


@router.post(
    "/v1/cours/{trimestre}/{sigle}/candidature",
    response_model=CoursFullResponse,
)
async def add_candidature_to_cours(
    *,
    cours: CurrentCourse,
    trimestre: int,
    payload: CandidaturePayload,
    context: Context,
):
    try:
        candidature_service = context.factory.create_candidature_service(trimestre)
        return await candidature_service.add_candidature_to_cours(
            cours=cours, payload=payload
        )
    except CandidatureExistsError:
        raise HTTPException(
            status_code=404, detail="Une candidature existe déjà pour ce candidat"
        )


@router.post("/v1/cours/{trimestre}/{sigle}/resumes", response_class=StreamingResponse)
async def download_multiple_resumes(
    *, trimestre: int, cours: CurrentCourse, context: Context
):
    try:
        candidature_service = context.factory.create_candidature_service(trimestre)
        return await candidature_service.get_resumes_for_course(cours)
    except NoStudentsFoundError:
        raise HTTPException(
            status_code=400, detail="Aucun étudiant trouvé pour le cours donné."
        )
