from fastapi import Depends, Path, Form, HTTPException, Request
from typing import Annotated, Optional

from src.dependencies.context import Context
from src.models import Etudiant


def _find_etudiant_or_raise(
    *,
    trimestre: int,
    context: Context,
    expect_existing: bool,
    email: str | None = None,
    code_permanent: str | None = None,
    etudiant_id: int | None = None,
) -> Optional[Etudiant]:
    etudiant_service = context.factory.create_etudiant_service(trimestre)
    if etudiant_id is None:
        assert code_permanent and email, (
            "Code permanent and email cannot be None if no etudiant is provided"
        )
        etudiant = etudiant_service.get_etudiant(
            code_permanent=code_permanent, email=email
        )
    else:
        etudiant = etudiant_service.get_etudiant_by_id(etudiant_id)

    if expect_existing and etudiant is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun étudiant trouvé avec ce code permanent et cet email.",
        )
    elif not expect_existing and etudiant is not None:
        raise HTTPException(
            status_code=400,
            detail="Une candidature existe déjà pour cet étudiant dans ce trimestre.",
        )

    return etudiant


def get_existing_etudiant(
    *,
    trimestre: Annotated[int, Path()],
    context: Context,
    etudiant_id: Annotated[int | None, Path()],
    code_permanent: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
) -> Etudiant | None:
    return _find_etudiant_or_raise(
        etudiant_id=etudiant_id,
        trimestre=trimestre,
        code_permanent=code_permanent,
        email=email,
        context=context,
        expect_existing=True,
    )


def ensure_etudiant_does_not_exist(
    *,
    trimestre: Annotated[int, Path()],
    context: Context,
    code_permanent: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    etudiant_id: Annotated[int | None, Path()] = None,
) -> None:
    print("asdasd", etudiant_id)
    _find_etudiant_or_raise(
        etudiant_id=etudiant_id,
        trimestre=trimestre,
        code_permanent=code_permanent,
        email=email,
        context=context,
        expect_existing=False,
    )


# Annotated types for cleaner injection
CurrentEtudiant = Annotated[Etudiant, Depends(get_existing_etudiant)]
EtudiantDoesNotExist = Annotated[None, Depends(ensure_etudiant_does_not_exist)]
