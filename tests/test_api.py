from pathlib import Path

from services.portfolio_chat import AnswerResult
from utils.rate_limit import RateLimitRule, reset_rate_limit_state


def test_perguntar_returns_answer(client, monkeypatch):
    reset_rate_limit_state()
    monkeypatch.setattr("utils.rate_limit._get_redis_client", lambda: None)
    monkeypatch.setattr(
        "routes.main_api.answer_portfolio_question",
        lambda question, user_id, language=None: AnswerResult(
            answer="Resposta ok",
            provider="openai",
            response_mode="generated",
        ),
    )

    response = client.post("/perguntar", json={"user_id": "u123", "pergunta": "Qual sua stack favorita?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["resposta"] == "Resposta ok"
    assert "metadata" in payload
    assert payload["metadata"]["label"] == "OpenAI"


def test_contact_route_persists_lead(client, monkeypatch):
    target_file = Path("data/test_contact_leads.jsonl")
    try:
        reset_rate_limit_state()
        monkeypatch.setattr("utils.rate_limit._get_redis_client", lambda: None)
        if target_file.exists():
            target_file.unlink()

        monkeypatch.setattr("routes.main_api.CONTACT_STORAGE_FILE", target_file)

        response = client.post(
            "/contato",
            json={
                "nome": "Recruiter Example",
                "empresa": "Acme",
                "email": "recruiter@example.com",
                "origem": "linkedin",
                "mensagem": "Gostaria de conversar.",
                "idioma": "pt-BR",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert target_file.exists()
    finally:
        target_file.unlink(missing_ok=True)


def test_admin_contacts_requires_token_and_returns_items(client, monkeypatch):
    target_file = Path("data/test_contact_leads_admin.jsonl")
    try:
        reset_rate_limit_state()
        monkeypatch.setattr("utils.rate_limit._get_redis_client", lambda: None)
        target_file.unlink(missing_ok=True)
        monkeypatch.setattr("routes.main_api.CONTACT_STORAGE_FILE", target_file)
        monkeypatch.setattr("routes.main_api.ADMIN_CONTACT_TOKEN", "secret-token")

        create_response = client.post(
            "/contato",
            json={
                "nome": "Recruiter Example",
                "empresa": "Acme",
                "email": "recruiter@example.com",
                "origem": "github",
                "mensagem": "Quero conversar.",
                "idioma": "pt-BR",
            },
        )
        assert create_response.status_code == 200

        unauthorized = client.get("/admin/contatos")
        assert unauthorized.status_code == 403

        authorized = client.get("/admin/contatos", headers={"x-admin-token": "secret-token"})
        assert authorized.status_code == 200
        payload = authorized.json()
        assert payload["items"][0]["email"] == "recruiter@example.com"
    finally:
        target_file.unlink(missing_ok=True)


def test_chat_rate_limit_returns_429(client, monkeypatch):
    reset_rate_limit_state()
    monkeypatch.setattr("utils.rate_limit._get_redis_client", lambda: None)
    monkeypatch.setattr(
        "routes.main_api.CHAT_RATE_LIMIT",
        RateLimitRule(scope="chat-test", limit=1, window_seconds=60, detail="Too many requests."),
    )
    monkeypatch.setattr(
        "routes.main_api.answer_portfolio_question",
        lambda question, user_id, language=None: AnswerResult(answer="Resposta ok", provider="rule"),
    )

    first = client.post("/perguntar", json={"user_id": "u123", "pergunta": "Qual sua stack favorita?"})
    second = client.post("/perguntar", json={"user_id": "u123", "pergunta": "Qual sua stack favorita?"})

    assert first.status_code == 200
    assert second.status_code == 429
