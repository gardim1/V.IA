from llm_provider import AllProvidersFailedError
from services.portfolio_chat import (
    AnswerResult,
    BUSY_RESPONSE,
    NOT_FOUND_RESPONSE,
    OUT_OF_SCOPE_RESPONSE,
    answer_portfolio_question,
)


class DummyHistory:
    def __init__(self, messages=None):
        self._messages = list(messages or [])

    @property
    def messages(self):
        return list(self._messages)

    def add_user_message(self, message):
        self._messages.append(type("Message", (), {"type": "human", "content": message})())

    def add_ai_message(self, message):
        self._messages.append(type("Message", (), {"type": "ai", "content": message})())


def test_small_talk_returns_rule_response(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Oi", "u1")

    assert isinstance(result, AnswerResult)
    assert "Vinicius" in result.answer
    assert result.provider == "rule"


def test_compound_cordial_message_returns_friendly_response(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Bom dia, tudo bem?", "u1")

    assert result.provider == "rule"
    assert result.answer != OUT_OF_SCOPE_RESPONSE
    assert "Vinicius" in result.answer or "ajudar" in result.answer


def test_thanks_variation_returns_friendly_response(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Obrigado viu!", "u1")

    assert result.provider == "rule"
    assert result.answer != OUT_OF_SCOPE_RESPONSE


def test_off_topic_returns_scope_message(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Me conta uma piada", "u1")

    assert result.answer == OUT_OF_SCOPE_RESPONSE
    assert result.provider == "rule"


def test_not_found_when_retrieval_is_empty(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr("services.portfolio_chat.search_documents", lambda *args, **kwargs: [])

    result = answer_portfolio_question("Qual sua stack favorita?", "u1")

    assert result.answer == NOT_FOUND_RESPONSE
    assert result.provider == "retrieval"


def test_provider_fallback_to_busy_message(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    fake_doc = type(
        "RetrievedDocument",
        (),
        {
            "document": type(
                "Document",
                (),
                {
                    "page_content": "Vinicius gosta de backend e IA.",
                    "metadata": {"source": "perfil.txt", "categoria": "HABILIDADES", "id": "1"},
                },
            )(),
            "score": 0.1,
        },
    )()

    monkeypatch.setattr("services.portfolio_chat.search_documents", lambda *args, **kwargs: [fake_doc])
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AllProvidersFailedError(["openai failed", "ollama failed"])
        ),
    )

    result = answer_portfolio_question("Qual sua stack favorita?", "u1")

    assert result.answer == BUSY_RESPONSE
    assert result.provider == "fallback_error"
