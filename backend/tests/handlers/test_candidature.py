from src.factory import Factory
from src.schemas import Etudiant, Campagne
from src.models.uqo import Campus
from fastapi.testclient import TestClient


def test_candidature(client: TestClient, factory: Factory):
    factory.session.add(Campagne(trimestre=20251))
    factory.session.add(
        Etudiant(
            code_permanent="TEST873003000",
            email="test.test@gmail.com",
            nom="Test",
            prenom="Test",
            cycle=3,
            campus=Campus.gat,
            programme="1234",
            trimestre=20251,
        )
    )
    factory.session.commit()

    response = client.get("/v1/20251/candidature")
    data = response.json()

    assert len(data) > 0

    assert 1 == 1


def test_candidature_2(client: TestClient, factory: Factory):
    factory.session.add(Campagne(trimestre=20251))
    factory.session.add(
        Etudiant(
            code_permanent="TEST873003000",
            email="test.test@gmail.com",
            nom="Test",
            prenom="Test",
            cycle=3,
            campus=Campus.gat,
            programme="1234",
            trimestre=20251,
        )
    )
    factory.session.commit()

    response = client.get("/v1/20251/candidature")
    data = response.json()

    assert len(data) > 0

    assert 1 == 1
