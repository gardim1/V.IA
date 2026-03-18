from services.portfolio_chat import AnswerResult
from utils.history import get_history


def test_history_saves_and_clear(client, monkeypatch):
    monkeypatch.setattr(
        "routes.main_api.answer_portfolio_question",
        lambda question, user_id, language=None: AnswerResult(answer="Ping ok", provider="rule"),
    )

    resp = client.post("/perguntar", json={"user_id": "test", "pergunta": "Ping?"})
    assert resp.status_code == 200

    history = get_history("test")
    history.add_user_message("Ping?")
    history.add_ai_message("Ping ok")

    resp = client.delete("/history/test")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
