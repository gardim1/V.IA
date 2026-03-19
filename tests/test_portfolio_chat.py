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


def _doc(content: str, categoria: str, source: str = "perfil.txt", score: float = 0.1):
    return type(
        "RetrievedDocument",
        (),
        {
            "document": type(
                "Document",
                (),
                {
                    "page_content": content,
                    "metadata": {"source": source, "categoria": categoria, "id": f"{source}-{categoria}"},
                },
            )(),
            "score": score,
        },
    )()


def _generation(text: str, provider: str = "openai"):
    return type("GenerationResult", (), {"text": text, "provider": provider, "errors": []})()


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
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Vinicius trabalha com backend, automacao e inteligencia artificial aplicada a problemas reais.",
                "HABILIDADES",
            )
        ],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AllProvidersFailedError(["openai failed", "ollama failed"])
        ),
    )

    result = answer_portfolio_question("Qual sua stack favorita?", "u1")

    assert result.answer == BUSY_RESPONSE
    assert result.provider == "fallback_error"


def test_hobbies_question_prefers_life_context_over_strengths(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda query, limit=6, filtro=None: [
            _doc(
                "Vinicius gosta de praticar esportes, fazer academia, correr, jogar, assistir animes e ler.",
                "VIDA_PESSOAL",
                source="vida_pessoal.txt",
                score=0.05,
            ),
            _doc(
                "Vinicius se destaca pela rapida capacidade de aprendizado, boa comunicacao e lideranca.",
                "HABILIDADES",
                source="habilidades.txt",
                score=0.07,
            ),
        ],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: _generation(
            "Os hobbies dele incluem esportes, academia, corrida, jogos, animes e leitura."
        ),
    )

    result = answer_portfolio_question("Quais sao os hobbies do Vinicius?", "u1")

    assert result.provider == "openai"
    assert result.response_mode == "generated"
    assert "hobbies" in result.answer.lower() or "esportes" in result.answer.lower()


def test_projects_question_stays_on_projects_topic(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda query, limit=6, filtro=None: [
            _doc(
                "Projeto de calculo de velocidade de bolinhas de ping-pong com visao computacional.",
                "PROJETOS",
                source="projetos.txt",
                score=0.04,
            ),
            _doc(
                "Vinicius tem 21 anos e mora em Santana de Parnaiba.",
                "IDENTIDADE",
                source="identidade.txt",
                score=0.05,
            ),
        ],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: _generation(
            "Entre os projetos relevantes estao a IA com RAG, o chat com Blazor e os projetos de visao computacional."
        ),
    )

    result = answer_portfolio_question("Quais projetos mais relevantes o Vinicius ja desenvolveu?", "u1")

    assert result.provider == "openai"
    assert "projetos" in result.answer.lower() or "rag" in result.answer.lower()
    assert "21 anos" not in result.answer.lower()


def test_generic_claude_question_is_out_of_scope(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())

    result = answer_portfolio_question("Quero saber sobre a IA Claude Code", "u1")

    assert result.answer == OUT_OF_SCOPE_RESPONSE
    assert result.provider == "rule"
    assert result.response_mode == "out_of_scope"


def test_subject_question_about_external_tool_with_unrelated_context_returns_not_found(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc("Vinicius gosta de backend, automacao e inteligencia artificial aplicada.", "HABILIDADES")
        ],
    )

    result = answer_portfolio_question("O Vinicius usa Claude Code?", "u1")

    assert result.answer == NOT_FOUND_RESPONSE
    assert result.provider == "retrieval"
    assert result.response_mode == "not_found"


def test_age_question_is_not_blocked_as_out_of_scope(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Nome completo: Vinicius Silva Gardim. Idade: 21 anos. Cidade: Santana de Parnaiba, Sao Paulo, Brasil.",
                "IDENTIDADE",
                source="identidade.txt",
                score=0.01,
            )
        ],
    )
    result = answer_portfolio_question("quantos anos ele tem", "u1")

    assert result.answer == "Vinicius tem 21 anos."
    assert result.provider == "rule"
    assert result.response_mode == "grounded_fact"


def test_formacao_question_can_use_grounded_fact(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Formação atual: Engenharia de Software na FIAP.\nVinicius cursa Engenharia de Software na FIAP.",
                "FORMACAO",
                source="formacao.txt",
                score=0.01,
            )
        ],
    )

    result = answer_portfolio_question("Qual formacao dele?", "u1")

    assert "Engenharia de Software" in result.answer
    assert result.provider == "rule"
    assert result.response_mode == "grounded_fact"


def test_language_question_can_use_grounded_fact(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Vinicius viveu um ano na Australia. Ele e fluente em ingles. Ele tem espanhol em nivel intermediario.",
                "IDENTIDADE",
                source="identidade.txt",
                score=0.01,
            )
        ],
    )

    result = answer_portfolio_question("Ele fala espanhol?", "u1")

    assert "espanhol" in result.answer.lower()
    assert result.provider == "rule"
    assert result.response_mode == "grounded_fact"


def test_abroad_question_can_use_grounded_fact(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Vinicius viveu um ano na Australia. Ele e fluente em ingles.",
                "IDENTIDADE",
                source="identidade.txt",
                score=0.01,
            )
        ],
    )

    result = answer_portfolio_question("O Vinicius morou fora do Brasil?", "u1")

    assert "Austrália" in result.answer or "Australia" in result.answer
    assert result.provider == "rule"
    assert result.response_mode == "grounded_fact"


def test_velocidade_question_does_not_match_age_topic(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Projeto de calculo de velocidade de bolinhas de ping-pong com base em visao computacional.",
                "PROJETOS",
                source="projetos.txt",
                score=0.03,
            ),
            _doc("Idade: 21 anos", "IDENTIDADE", source="identidade.txt", score=0.2),
        ],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: _generation(
            "Sim. Ele desenvolveu um projeto para calcular a velocidade de bolinhas de ping-pong usando visao computacional."
        ),
    )

    result = answer_portfolio_question("Sobre esse calculo de velocidade de bolinhas de ping-pong, tem como me mostrar?", "u1")

    assert "21 anos" not in result.answer.lower()
    assert "ping-pong" in result.answer.lower()


def test_teamwork_question_generates_answer_from_behavior_context(monkeypatch):
    monkeypatch.setattr("services.portfolio_chat.get_history", lambda user_id: DummyHistory())
    monkeypatch.setattr(
        "services.portfolio_chat.search_documents",
        lambda *args, **kwargs: [
            _doc(
                "Vinicius trabalha bem em equipe, tem boa comunicacao e costuma ajudar outros membros do time.",
                "HABILIDADES",
                source="habilidades.txt",
                score=0.02,
            ),
            _doc(
                "Costuma dividir bem tarefas, colaborar com outros membros e ajudar quando alguem tem dificuldade.",
                "CARREIRA",
                source="carreira.txt",
                score=0.04,
            ),
        ],
    )
    monkeypatch.setattr(
        "services.portfolio_chat.invoke_with_fallback",
        lambda *args, **kwargs: _generation(
            "Vinicius trabalha bem em equipe, se comunica com clareza e costuma colaborar de forma ativa."
        ),
    )

    result = answer_portfolio_question("Como o Vinicius trabalha em equipe e se comunica?", "u1")

    assert result.provider == "openai"
    assert "equipe" in result.answer.lower() or "comunica" in result.answer.lower()
