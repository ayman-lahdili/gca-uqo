from fastapi.testclient import TestClient

def test_get_uqo_programmes(client: TestClient):
    response = client.get("/v1/uqo/programmes?departement=INFOR&cycle=1")
    assert response.status_code == 200

def test_get_uqo_courses(client: TestClient):
    response = client.get("/v1/uqo/cours?departement=DII")
    assert response.status_code == 200

def test_get_uqo_horaire(client: TestClient):
    response = client.get("/v1/uqo/20231/horaire")
    assert response.status_code == 200