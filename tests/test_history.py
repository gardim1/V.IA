def test_history_saves_and_clear(client):
    resp = client.post("/perguntar", json={"user_id": "test", "pergunta": "Ping?"})
    assert resp.status_code == 200

    resp = client.delete("/history/test")
    assert resp.json()["deleted"] == True