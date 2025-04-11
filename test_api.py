from fastapi.testclient import TestClient
from main_api import app

client = TestClient(app)

def test_perguntar():
    payload = {"pergunta": "O que é o sistema TMS?"}
    response = client.post("/perguntar", json=payload)
    
    assert response.status_code == 200
    json_data = response.json()
    assert "resposta" in json_data
    assert len(json_data["resposta"]) > 0
