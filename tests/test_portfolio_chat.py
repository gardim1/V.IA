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
    assert result.response_mode == "small_talk"


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
    assert result.response_mode == "out_of_scope"


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


def test_direct_answer_from_retrieved_context_bypasses_llm(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr("services.portfolio_chat._load_direct_faq_entries", lambda: [])

    fake_doc = type(
        "RetrievedDocument",
        (),
        {
            "document": type(
                "Document",
                (),
                {
                    "page_content": (
                        "Pergunta frequente: Onde o Vinicius quer estar em 5 anos?\n\n"
                        "Resposta direta:\n"
                        "Ele pretende estar consolidado na area de tecnologia, com foco em backend e inteligencia artificial, "
                        "atuando em nivel senior ou liderando projetos.\n\n"
                        "Outras informacoes:"
                    ),
                    "metadata": {"source": "faq_recrutador.txt", "categoria": "IDENTIDADE", "id": "faq-1"},
                },
            )(),
            "score": 0.01,
        },
    )()

    monkeypatch.setattr("services.portfolio_chat.search_documents", lambda *args, **kwargs: [fake_doc])
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM should not be called for direct answers")),
    )

    result = answer_portfolio_question("Onde o Vinicius quer estar em 5 anos?", "u1")

    assert "consolidado na area de tecnologia" in result.answer
    assert result.provider == "rule"
    assert result.response_mode == "direct_answer"


def test_direct_answer_does_not_trigger_for_unrelated_question(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr("services.portfolio_chat._load_direct_faq_entries", lambda: [])

    fake_doc = type(
        "RetrievedDocument",
        (),
        {
            "document": type(
                "Document",
                (),
                {
                    "page_content": (
                        "Pergunta frequente: Onde o Vinicius quer estar em 5 anos?\n\n"
                        "Resposta direta:\n"
                        "Ele pretende estar consolidado na area de tecnologia, com foco em backend e inteligencia artificial.\n"
                    ),
                    "metadata": {"source": "faq_recrutador.txt", "categoria": "IDENTIDADE", "id": "faq-1"},
                },
            )(),
            "score": 0.01,
        },
    )()

    monkeypatch.setattr("services.portfolio_chat.search_documents", lambda *args, **kwargs: [fake_doc])
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: type(
            "GenerationResult",
            (),
            {"text": "Resposta da IA", "provider": "openai", "errors": []},
        )(),
    )

    result = answer_portfolio_question("Quais projetos ele entregou?", "u1")

    assert result.answer == "Resposta da IA"
    assert result.provider == "openai"


def test_generic_claude_question_is_out_of_scope(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Quero saber sobre a IA Claude Code", "u1")

    assert result.answer == OUT_OF_SCOPE_RESPONSE
    assert result.provider == "rule"
    assert result.response_mode == "out_of_scope"


def test_direct_catalog_answer_handles_short_factual_question(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat._load_direct_faq_entries",
        lambda: [("Qual a idade do Vinicius?", "Vinicius tem 21 anos.")],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Retrieval should not run for strict FAQ match")),
    )

    result = answer_portfolio_question("Qual idade dele?", "u1")

    assert result.answer == "Vinicius tem 21 anos."
    assert result.provider == "rule"
    assert result.response_mode == "direct_answer"


def test_parse_direct_faq_entries_supports_multiple_entries():
    from services.portfolio_chat import _parse_direct_faq_entries

    content = (
        "Pergunta frequente: Qual a idade do Vinicius?\n\n"
        "Resposta direta:\n"
        "Vinicius tem 21 anos.\n\n"
        "Pergunta frequente: Qual a formacao do Vinicius?\n\n"
        "Resposta direta:\n"
        "Vinicius cursa Engenharia de Software na FIAP.\n"
    )

    assert _parse_direct_faq_entries(content) == [
        ("Qual a idade do Vinicius?", "Vinicius tem 21 anos."),
        ("Qual a formacao do Vinicius?", "Vinicius cursa Engenharia de Software na FIAP."),
    ]
