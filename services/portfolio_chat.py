from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from llm_provider import AllProvidersFailedError, invoke_with_fallback
from utils.history import get_history
from vector_utils import RetrievedDocument, search_documents

DEFAULT_LANGUAGE = "pt-BR"

LANGUAGE_COPY = {
    "pt-BR": {
        "target_language": "português brasileiro",
        "out_of_scope": "Desculpe, eu sou o Vinnie e respondo apenas perguntas sobre Vinicius Silva Gardim.",
        "not_found": "Desculpe, não encontrei essa informação sobre Vinicius Silva Gardim.",
        "busy": "O Vinnie está com muita demanda agora. Tente novamente mais tarde.",
        "small_talk": {
            "oi": "Oi! Eu sou o Vinnie, assistente do Vinicius. Pode perguntar qualquer coisa sobre ele. 🙂",
            "ola": "Olá! Eu sou o Vinnie, assistente do Vinicius. Pode perguntar qualquer coisa sobre ele. 🙂",
            "hi": "Oi! Eu sou o Vinnie, assistente do Vinicius. Pode perguntar qualquer coisa sobre ele. 🙂",
            "hello": "Oi! Eu sou o Vinnie, assistente do Vinicius. Pode perguntar qualquer coisa sobre ele. 🙂",
            "bom dia": "Bom dia! Como posso te ajudar sobre o Vinicius hoje? 🙂",
            "boa tarde": "Boa tarde! Como posso te ajudar sobre o Vinicius hoje? 🙂",
            "boa noite": "Boa noite! Como posso te ajudar sobre o Vinicius hoje? 🙂",
            "tudo bem": "Tudo bem por aqui! Quer saber algo sobre o Vinicius?",
            "valeu": "De nada! Se quiser, pode perguntar algo sobre o Vinicius. 🙂",
            "obrigado": "Imagina! Se quiser, pode perguntar algo sobre o Vinicius. 🙂",
            "obrigada": "Imagina! Se quiser, pode perguntar algo sobre o Vinicius. 🙂",
            "thanks": "Imagina! Se quiser, pode perguntar algo sobre o Vinicius. 🙂",
            "thank you": "Imagina! Se quiser, pode perguntar algo sobre o Vinicius. 🙂",
            "tchau": "Tchau! Quando quiser, pode voltar e perguntar mais sobre o Vinicius. 👋",
        },
    },
    "en-US": {
        "target_language": "English",
        "out_of_scope": "Sorry, I am Vinnie and I only answer questions about Vinicius Silva Gardim.",
        "not_found": "Sorry, I could not find that information about Vinicius Silva Gardim.",
        "busy": "Vinnie is handling a lot of traffic right now. Please try again later.",
        "small_talk": {
            "oi": "Hi! I am Vinnie, Vinicius' assistant. You can ask me anything about him. 🙂",
            "ola": "Hi! I am Vinnie, Vinicius' assistant. You can ask me anything about him. 🙂",
            "hi": "Hi! I am Vinnie, Vinicius' assistant. You can ask me anything about him. 🙂",
            "hello": "Hi! I am Vinnie, Vinicius' assistant. You can ask me anything about him. 🙂",
            "bom dia": "Hi! How can I help you learn more about Vinicius today? 🙂",
            "boa tarde": "Hi! How can I help you learn more about Vinicius today? 🙂",
            "boa noite": "Hi! How can I help you learn more about Vinicius today? 🙂",
            "tudo bem": "Doing well here. Want to know something about Vinicius?",
            "valeu": "Anytime! Feel free to ask something about Vinicius. 🙂",
            "obrigado": "Anytime! Feel free to ask something about Vinicius. 🙂",
            "obrigada": "Anytime! Feel free to ask something about Vinicius. 🙂",
            "thanks": "Anytime! Feel free to ask something about Vinicius. 🙂",
            "thank you": "Anytime! Feel free to ask something about Vinicius. 🙂",
            "tchau": "Bye! Whenever you want, you can come back and ask more about Vinicius. 👋",
        },
    },
}

SMALL_TALK_ALIASES = {
    "opa": "oi",
    "oii": "oi",
    "e ai": "oi",
    "eae": "oi",
    "hey": "hello",
    "good morning": "bom dia",
    "good afternoon": "boa tarde",
    "good evening": "boa noite",
    "bom dia tudo bem": "bom dia",
    "boa tarde tudo bem": "boa tarde",
    "boa noite tudo bem": "boa noite",
    "oi tudo bem": "oi",
    "ola tudo bem": "ola",
    "tudo bom": "tudo bem",
    "como vai": "tudo bem",
    "blz": "tudo bem",
    "beleza": "tudo bem",
    "obg": "obrigado",
    "obrigadao": "obrigado",
    "agradecido": "obrigado",
    "ate mais": "tchau",
    "ate logo": "tchau",
    "falou": "tchau",
    "flw": "tchau",
    "bye": "tchau",
    "see you": "tchau",
    "see ya": "tchau",
}

SMALL_TALK_ALLOWED_TOKENS = {
    "oi",
    "ola",
    "opa",
    "oii",
    "e",
    "ai",
    "eae",
    "hey",
    "hi",
    "hello",
    "bom",
    "boa",
    "dia",
    "tarde",
    "noite",
    "good",
    "morning",
    "afternoon",
    "evening",
    "tudo",
    "bem",
    "como",
    "vai",
    "blz",
    "beleza",
    "valeu",
    "obrigado",
    "obrigada",
    "obrigadao",
    "obg",
    "thanks",
    "thank",
    "you",
    "agradecido",
    "tchau",
    "ate",
    "mais",
    "logo",
    "falou",
    "flw",
    "bye",
    "see",
    "ya",
    "viu",
}

DIRECT_ANSWER_STOPWORDS = {
    "o",
    "a",
    "os",
    "as",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "e",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "um",
    "uma",
    "me",
    "sobre",
    "quero",
    "saber",
    "mais",
    "ele",
    "dele",
    "dela",
    "para",
    "por",
    "que",
    "qual",
    "quais",
    "como",
    "onde",
    "nos",
    "nas",
}

DIRECT_ANSWER_INTENTS = {
    "idade": ("idade", "quantos anos"),
    "formacao": ("formacao", "faculdade", "curso", "fiap"),
    "objetivos_5_anos": ("5 anos", "proximos 5 anos"),
    "experiencias": ("experiencia profissional", "experiencias profissionais", "experiencias passadas", "trajetoria profissional"),
    "pontos_fortes": ("pontos fortes",),
    "pontos_melhoria": ("pontos de melhoria",),
    "trabalhar_empresa": ("trabalhar nesta empresa",),
    "ultimo_emprego": ("ultimo emprego",),
    "pressao": ("pressao",),
    "equipe": ("equipe", "trabalha bem em equipe"),
    "desafio_tecnico": ("desafio tecnico",),
    "contratar": ("contratar",),
}

OUT_OF_SCOPE_RESPONSE = LANGUAGE_COPY[DEFAULT_LANGUAGE]["out_of_scope"]
NOT_FOUND_RESPONSE = LANGUAGE_COPY[DEFAULT_LANGUAGE]["not_found"]
BUSY_RESPONSE = LANGUAGE_COPY[DEFAULT_LANGUAGE]["busy"]

PORTFOLIO_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Você é o Vinnie, o assistente virtual criado por Vinicius Silva Gardim. "
                "Você NÃO é o Vinicius, não fala em nome dele e não se confunde com ele. "
                "Seu papel é apresentar e explicar informações sobre Vinicius com clareza. "
                "Use somente o contexto confirmado abaixo. "
                "Considere contexto semanticamente equivalente como suficiente para responder. "
                "Por exemplo, perguntas sobre futuro, objetivos ou próximos 5 anos podem ser respondidas com trechos como 'Visão de longo prazo (5 anos)' ou seções de objetivos, mesmo que a formulação não seja idêntica. "
                "Se o contexto trouxer uma seção com 'Resposta direta:', priorize essa resposta e adapte apenas o mínimo necessário para soar natural. "
                'Se a resposta não estiver claramente no contexto, responda exatamente: "{not_found_response}" '
                "Nunca invente fatos, nunca fale de documentos internos e nunca se passe pelo Vinicius. "
                "Se o contexto tiver listas, use essas listas para responder de forma objetiva. "
                "Quando ajudar a leitura, você pode usar Markdown leve, como títulos curtos, listas e **negrito**. "
                "Use emoji com moderação, no máximo 1 quando soar natural. "
                "Um toque leve de humor ou uma piada curta só é permitido quando for claramente conveniente e não atrapalhar o tom profissional."
            ),
        ),
        (
            "human",
            (
                "Histórico recente:\n{chat_history}\n\n"
                "Pergunta original:\n{original_question}\n\n"
                "Pergunta reescrita para busca:\n{rewritten_question}\n\n"
                "Contexto confirmado:\n{context}\n\n"
                "Responda em {target_language}, de forma clara e natural, sem mencionar contexto ou documentos."
            ),
        ),
    ]
)

CATEGORY_KEYWORDS = {
    "IDENTIDADE": [
        "quem e voce",
        "quem eh voce",
        "who are you",
        "tell me about yourself",
        "about you",
        "your name",
        "your age",
        "se apresenta",
        "se apresente",
        "seu nome",
        "idade",
        "sobre voce",
        "apresentacao",
    ],
    "VIDA_PESSOAL": [
        "rotina",
        "dia a dia",
        "tempo livre",
        "fim de semana",
        "final de semana",
        "hobby",
        "hobbies",
        "free time",
        "day to day",
        "outside work",
        "personal life",
        "vida pessoal",
        "fora do trabalho",
        "curte",
        "gosta de fazer",
    ],
    "RELACIONAMENTOS": [
        "namora",
        "namoro",
        "namorada",
        "relacionamento",
        "carol",
        "vida amorosa",
        "relationship",
        "girlfriend",
        "dating",
    ],
    "FORMACAO": [
        "faculdade",
        "formacao",
        "f i a p",
        "fiap",
        "estuda",
        "estudos",
        "curso",
        "semestre",
        "college",
        "university",
        "education",
        "degree",
        "studies",
    ],
    "CARREIRA": [
        "trabalha",
        "trabalho",
        "carreira",
        "experiencia",
        "experiencias",
        "experiencia profissional",
        "experiencias profissionais",
        "experiencias passadas",
        "passado profissional",
        "trajetoria profissional",
        "historico profissional",
        "antes disso",
        "anteriormente",
        "suporte",
        "desenvolvedor junior",
        "sislogica",
        "curriculo",
        "empresa",
        "emprego",
        "work",
        "career",
        "experience",
        "past experience",
        "past experiences",
        "professional experience",
        "professional background",
        "company",
        "job",
        "resume",
    ],
    "PROJETOS": [
        "projeto",
        "projetos",
        "portfolio",
        "rag",
        "api",
        "apis",
        "collaborate",
        "chatbot",
        "automacao",
        "automacoes",
        "v ia",
        "vinnie",
        "project",
        "projects",
        "automation",
        "automations",
    ],
    "HABILIDADES": [
        "stack",
        "tecnologia",
        "tecnologias",
        "habilidade",
        "habilidades",
        "diferencial",
        "diferenciais",
        "problema que resolve",
        "problemas que resolve",
        "problemas resolve",
        "problemas o vinicius resolve",
        "solve",
        "solves",
        "linguagem",
        "linguagens",
        "framework",
        "frameworks",
        "ferramenta",
        "ferramentas",
        "biblioteca",
        "bibliotecas",
        "skill",
        "skills",
        "technology",
        "technologies",
        "language",
        "languages",
        "tool",
        "tools",
        "library",
        "libraries",
        "python",
        "java",
        "c#",
        "sql",
        "react",
        "fastapi",
        "docker",
        "langchain",
        "blazor",
        "ia generativa",
    ],
    "OBJETIVOS": [
        "objetivo",
        "objetivos",
        "meta",
        "metas",
        "planos",
        "futuro",
        "roadmap",
        "cto",
        "ceo",
        "goal",
        "goals",
        "future",
        "plan",
        "plans",
    ],
    "PREFERENCIAS": [
        "prefere",
        "preferencia",
        "preferencias",
        "estilo",
        "forma de pensar",
        "como pensa",
        "mindset",
        "gosto",
        "jeito",
        "como gosta",
        "prefer",
        "preference",
        "preferences",
        "style",
        "likes to",
    ],
}

OFF_TOPIC_PATTERNS = [
    "receita",
    "capital da",
    "previsao do tempo",
    "clima",
    "temperatura",
    "piada",
    "poema",
    "poesia",
    "me conta uma historia",
    "traduza",
    "traduz",
    "resuma esse texto",
    "quem ganhou",
    "resultado do jogo",
    "weather",
    "recipe",
    "translate",
    "summarize this text",
    "who won",
    "score of the game",
]

EXTERNAL_GENERAL_TECH_PATTERNS = [
    "claude code",
    "claude",
    "chatgpt",
    "gpt",
    "gemini",
    "cursor",
    "copilot",
    "windsurf",
    "deepseek",
]


@dataclass
class AnswerResult:
    answer: str
    provider: str
    category_hint: str | None = None
    response_mode: str | None = None
    used_fallback: bool = False
    rewritten_question: str | None = None
    retrieved_docs: list[Document] = field(default_factory=list)
    provider_errors: list[str] = field(default_factory=list)


def _normalize_language(language: str | None) -> str:
    normalized = (language or DEFAULT_LANGUAGE).strip().lower()
    if normalized.startswith("en"):
        return "en-US"
    return "pt-BR"


def _get_language_copy(language: str | None) -> dict:
    return LANGUAGE_COPY[_normalize_language(language)]


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _strip_for_small_talk(normalized_question: str) -> str:
    stripped = re.sub(r"[^a-z0-9\s#]", " ", normalized_question)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def _resolve_small_talk_key(normalized_question: str) -> str | None:
    stripped = _strip_for_small_talk(normalized_question)
    if not stripped:
        return None

    for language in LANGUAGE_COPY:
        if stripped in LANGUAGE_COPY[language]["small_talk"]:
            return stripped

    alias = SMALL_TALK_ALIASES.get(stripped)
    if alias:
        return alias

    tokens = stripped.split()
    if not tokens or len(tokens) > 8:
        return None

    if any(token not in SMALL_TALK_ALLOWED_TOKENS for token in tokens):
        return None

    if "bom dia" in stripped or "good morning" in stripped:
        return "bom dia"

    if "boa tarde" in stripped or "good afternoon" in stripped:
        return "boa tarde"

    if "boa noite" in stripped or "good evening" in stripped:
        return "boa noite"

    if "tudo bem" in stripped or "tudo bom" in stripped or "como vai" in stripped:
        return "tudo bem"

    if any(word in stripped for word in ("obrigad", "valeu", "thanks", "thank you", "obg", "agradecido")):
        return "obrigado"

    if any(word in stripped for word in ("tchau", "falou", "ate mais", "ate logo", "bye", "see you", "see ya")):
        return "tchau"

    if any(word in stripped for word in ("oi", "ola", "opa", "hi", "hello", "hey", "e ai", "eae")):
        return "oi"

    return None


def _is_small_talk(normalized_question: str) -> bool:
    return _resolve_small_talk_key(normalized_question) is not None


def _build_small_talk_answer(normalized_question: str, language: str) -> str:
    resolved_key = _resolve_small_talk_key(normalized_question) or "oi"
    return LANGUAGE_COPY[language]["small_talk"].get(resolved_key, LANGUAGE_COPY[language]["small_talk"]["oi"])


def _looks_like_follow_up(normalized_question: str) -> bool:
    return bool(
        re.match(r"^(e\b|e quanto|e nisso|e isso|e nessa|e nesse|sobre isso|qual deles|e com)", normalized_question)
    )


def _keyword_matches(normalized_question: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in normalized_question

    if keyword.isalnum():
        return bool(re.search(rf"\b{re.escape(keyword)}\b", normalized_question))

    return keyword in normalized_question


def _classify_question(normalized_question: str) -> str | None:
    best_category: str | None = None
    best_score = 0
    best_keyword_size = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        keyword_size = 0
        for keyword in keywords:
            if _keyword_matches(normalized_question, keyword):
                score += 1
                keyword_size = max(keyword_size, len(keyword))

        if score > best_score or (score == best_score and keyword_size > best_keyword_size):
            best_category = category
            best_score = score
            best_keyword_size = keyword_size

    if best_category:
        return best_category

    if (
        "vinicius" in normalized_question
        or "gardim" in normalized_question
        or "v ia" in normalized_question
        or "vinnie" in normalized_question
    ):
        return "IDENTIDADE"

    if "voce" in normalized_question or "seu " in normalized_question or "sua " in normalized_question:
        return "IDENTIDADE"

    return None


def _is_scope_question(normalized_question: str, previous_user_question: str) -> bool:
    if _classify_question(normalized_question):
        return True

    if _extract_direct_intent(normalized_question):
        return True

    if _looks_like_follow_up(normalized_question) and previous_user_question:
        return True

    return False


def _is_obviously_off_topic(normalized_question: str) -> bool:
    return any(pattern in normalized_question for pattern in OFF_TOPIC_PATTERNS)


def _mentions_portfolio_subject(normalized_question: str, previous_user_question: str) -> bool:
    if any(name in normalized_question for name in ("vinicius", "gardim", "vinnie", "v ia")):
        return True

    tokens = set(_strip_for_small_talk(normalized_question).split())
    if tokens & {"ele", "dele", "seu", "sua", "him", "his"}:
        return True

    if previous_user_question.strip():
        return True

    return False


def _is_external_general_question(normalized_question: str, previous_user_question: str) -> bool:
    if not any(pattern in normalized_question for pattern in EXTERNAL_GENERAL_TECH_PATTERNS):
        return False

    return not _mentions_portfolio_subject(normalized_question, previous_user_question)


def _matched_external_general_pattern(normalized_question: str) -> str | None:
    for pattern in EXTERNAL_GENERAL_TECH_PATTERNS:
        if pattern in normalized_question:
            return pattern
    return None


def _context_mentions_external_pattern(retrieved_docs: list[RetrievedDocument], pattern: str) -> bool:
    if not pattern:
        return False

    for item in retrieved_docs[:4]:
        normalized_content = _normalize_text(item.document.page_content)
        if pattern in normalized_content:
            return True

    return False


def _rewrite_question(question: str, previous_user_question: str) -> str:
    if not previous_user_question:
        return question.strip()

    normalized_question = _normalize_text(question)
    previous_user_question = previous_user_question.strip()

    if normalized_question.startswith("e "):
        complemento = question.strip()[2:].strip(" ?")
        base = previous_user_question.rstrip(" ?")
        return f"{base} {complemento}?"

    if _looks_like_follow_up(normalized_question):
        return f"Contexto da pergunta anterior: {previous_user_question}. Nova pergunta: {question.strip()}"

    return question.strip()


def _format_chat_history(messages, limit: int = 6) -> str:
    if not messages:
        return "Sem histórico relevante."

    selected_messages = messages[-limit:]
    lines: list[str] = []
    for message in selected_messages:
        role = "Usuário" if getattr(message, "type", "") == "human" else "Vinnie"
        content = getattr(message, "content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_context(retrieved_docs: list[RetrievedDocument], top_k: int = 3) -> str:
    lines: list[str] = []
    for index, item in enumerate(retrieved_docs[:top_k], start=1):
        source = item.document.metadata.get("source", "desconhecida")
        category = item.document.metadata.get("categoria", "GERAL")
        score_text = "n/a" if item.score is None else f"{item.score:.4f}"
        lines.append(f"[Trecho {index}]")
        lines.append(f"Fonte: {source}")
        lines.append(f"Categoria: {category}")
        lines.append(f"Score: {score_text}")
        lines.append(item.document.page_content.strip())
        lines.append("")
    return "\n".join(lines).strip()


def _merge_results(*groups: list[RetrievedDocument]) -> list[RetrievedDocument]:
    merged: dict[str, RetrievedDocument] = {}
    for group in groups:
        for item in group:
            doc_id = item.document.metadata.get("id") or item.document.metadata.get("source") or item.document.page_content
            previous = merged.get(doc_id)
            if previous is None:
                merged[doc_id] = item
                continue

            if previous.score is None or (item.score is not None and item.score < previous.score):
                merged[doc_id] = item

    return sorted(merged.values(), key=lambda item: item.score if item.score is not None else 999999)


def _is_useful_chunk(item: RetrievedDocument) -> bool:
    content = item.document.page_content.strip()
    if len(content) < 40:
        return False

    plain_lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(plain_lines) == 1 and plain_lines[0].isupper():
        return False

    return True


def _extract_direct_answer_from_text(content: str) -> str | None:
    marker = "Resposta direta:"
    if marker not in content:
        return None

    tail = content.split(marker, 1)[1].strip()
    if not tail:
        return None

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", tail) if paragraph.strip()]
    if not paragraphs:
        return None

    collected: list[str] = []
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        if lowered.startswith("pergunta frequente:"):
            break
        if paragraph.startswith("====="):
            break
        if paragraph.endswith(":") and len(paragraph) < 120:
            break
        collected.append(paragraph)
        if len(collected) >= 3:
            break

    answer = "\n\n".join(collected).strip()
    return answer or None


def _extract_direct_question_from_text(content: str) -> str | None:
    marker = "Pergunta frequente:"
    if marker not in content:
        return None

    head = content.split(marker, 1)[1].strip()
    if not head:
        return None

    first_line = head.splitlines()[0].strip()
    return first_line or None


def _parse_direct_faq_entries(content: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"Pergunta frequente:\s*(.+?)\n\s*\nResposta direta:\s*(.+?)(?=\n\s*\nPergunta frequente:|\Z)",
        re.DOTALL,
    )
    entries: list[tuple[str, str]] = []

    for question, answer in pattern.findall(content):
        cleaned_question = question.strip().splitlines()[0].strip()
        cleaned_answer = answer.strip()
        if cleaned_question and cleaned_answer:
            entries.append((cleaned_question, cleaned_answer))

    return entries


def _tokenize_direct_match(text: str) -> set[str]:
    normalized = _normalize_text(text)
    return {
        token
        for token in normalized.split()
        if len(token) >= 3 and token not in DIRECT_ANSWER_STOPWORDS
    }


def _extract_direct_intent(text: str) -> str | None:
    normalized = _normalize_text(text)
    for intent, phrases in DIRECT_ANSWER_INTENTS.items():
        if any(phrase in normalized for phrase in phrases):
            return intent
    return None


def _faq_matches_question(question: str, faq_question: str) -> bool:
    normalized_question = _normalize_text(question)
    normalized_faq_question = _normalize_text(faq_question)

    question_intent = _extract_direct_intent(question)
    faq_intent = _extract_direct_intent(faq_question)
    if question_intent and faq_intent and question_intent == faq_intent:
        return True

    if normalized_question == normalized_faq_question:
        return True

    if len(normalized_question) >= 18 and normalized_question in normalized_faq_question:
        return True

    if len(normalized_faq_question) >= 18 and normalized_faq_question in normalized_question:
        return True

    question_tokens = _tokenize_direct_match(question)
    faq_tokens = _tokenize_direct_match(faq_question)
    if not question_tokens or not faq_tokens:
        return False

    shared_tokens = question_tokens & faq_tokens
    if len(shared_tokens) < 2:
        return False

    overlap = len(shared_tokens) / min(len(question_tokens), len(faq_tokens))
    return overlap >= 0.5


@lru_cache(maxsize=1)
def _load_direct_faq_entries() -> list[tuple[str, str]]:
    faq_dir = Path(__file__).resolve().parent.parent / "conteudos_vini_02"
    entries: list[tuple[str, str]] = []

    if not faq_dir.exists():
        return entries

    for path in faq_dir.glob("*.txt"):
        content = path.read_text(encoding="utf-8")
        parsed_entries = _parse_direct_faq_entries(content)
        if parsed_entries:
            entries.extend(parsed_entries)
            continue

        for section in content.split("====="):
            faq_question = _extract_direct_question_from_text(section)
            answer = _extract_direct_answer_from_text(section)
            if faq_question and answer and len(answer) >= 20:
                entries.append((faq_question, answer))

    return entries


def _lookup_direct_answer(question: str) -> str | None:
    for faq_question, answer in _load_direct_faq_entries():
        if _faq_matches_question(question, faq_question):
            return answer
    return None


def _extract_direct_answer(retrieved_docs: list[RetrievedDocument], question: str) -> str | None:
    for item in retrieved_docs[:4]:
        faq_question = _extract_direct_question_from_text(item.document.page_content)
        answer = _extract_direct_answer_from_text(item.document.page_content)
        if faq_question and answer and len(answer) >= 40 and _faq_matches_question(question, faq_question):
            return answer

    return None


def _retrieve_context(question: str, category_hint: str | None) -> list[RetrievedDocument]:
    global_results = search_documents(question, limit=6)
    if not category_hint:
        return [item for item in global_results if _is_useful_chunk(item)]

    hinted_results = search_documents(question, limit=4, filtro=category_hint)
    hinted_filtered = [item for item in hinted_results if _is_useful_chunk(item)]
    global_filtered = [item for item in global_results if _is_useful_chunk(item)]

    ordered: list[RetrievedDocument] = []
    seen_ids: set[str] = set()
    for group in (hinted_filtered, global_filtered):
        for item in group:
            doc_id = item.document.metadata.get("id") or item.document.metadata.get("source") or item.document.page_content
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            ordered.append(item)

    return ordered or _merge_results(hinted_results, global_results)


def answer_portfolio_question(question: str, user_id: str, language: str | None = DEFAULT_LANGUAGE) -> AnswerResult:
    if not user_id:
        raise ValueError("user_id is required")

    normalized_language = _normalize_language(language)
    copy = _get_language_copy(normalized_language)
    history = get_history(user_id)
    history_messages = history.messages
    previous_user_question = next(
        (message.content for message in reversed(history_messages) if getattr(message, "type", "") == "human"),
        "",
    )

    normalized_question = _normalize_text(question)

    if _is_small_talk(normalized_question):
        answer = _build_small_talk_answer(normalized_question, normalized_language)
        history.add_user_message(question)
        history.add_ai_message(answer)
        return AnswerResult(
            answer=answer,
            provider="rule",
            response_mode="small_talk",
            rewritten_question=question.strip(),
        )

    if _is_obviously_off_topic(normalized_question):
        history.add_user_message(question)
        history.add_ai_message(copy["out_of_scope"])
        return AnswerResult(
            answer=copy["out_of_scope"],
            provider="rule",
            response_mode="out_of_scope",
            rewritten_question=question.strip(),
        )

    if _is_external_general_question(normalized_question, previous_user_question):
        history.add_user_message(question)
        history.add_ai_message(copy["out_of_scope"])
        return AnswerResult(
            answer=copy["out_of_scope"],
            provider="rule",
            response_mode="out_of_scope",
            rewritten_question=question.strip(),
        )

    rewritten_question = _rewrite_question(question, previous_user_question)
    external_pattern = _matched_external_general_pattern(_normalize_text(rewritten_question))
    direct_catalog_answer = _lookup_direct_answer(rewritten_question)
    if direct_catalog_answer:
        history.add_user_message(question)
        history.add_ai_message(direct_catalog_answer)
        return AnswerResult(
            answer=direct_catalog_answer,
            provider="rule",
            response_mode="direct_answer",
            rewritten_question=rewritten_question,
        )

    category_hint = _classify_question(_normalize_text(rewritten_question))
    retrieved_docs = _retrieve_context(rewritten_question, category_hint)

    if not retrieved_docs:
        history.add_user_message(question)
        history.add_ai_message(copy["not_found"])
        return AnswerResult(
            answer=copy["not_found"],
            provider="retrieval",
            category_hint=category_hint,
            response_mode="not_found",
            rewritten_question=rewritten_question,
        )

    if external_pattern and not _context_mentions_external_pattern(retrieved_docs, external_pattern):
        history.add_user_message(question)
        history.add_ai_message(copy["not_found"])
        return AnswerResult(
            answer=copy["not_found"],
            provider="retrieval",
            category_hint=category_hint,
            response_mode="not_found",
            rewritten_question=rewritten_question,
            retrieved_docs=[item.document for item in retrieved_docs[:3]],
        )

    direct_answer = _extract_direct_answer(retrieved_docs, rewritten_question)
    if direct_answer:
        history.add_user_message(question)
        history.add_ai_message(direct_answer)
        return AnswerResult(
            answer=direct_answer,
            provider="rule",
            category_hint=category_hint,
            response_mode="direct_answer",
            rewritten_question=rewritten_question,
            retrieved_docs=[item.document for item in retrieved_docs[:3]],
        )

    prompt_variables = {
        "chat_history": _format_chat_history(history_messages),
        "original_question": question.strip(),
        "rewritten_question": rewritten_question,
        "context": _format_context(retrieved_docs, top_k=3),
        "target_language": copy["target_language"],
        "not_found_response": copy["not_found"],
    }

    try:
        generation = invoke_with_fallback(PORTFOLIO_PROMPT, prompt_variables, temperature=0.2)
        answer = generation.text or copy["busy"]
        history.add_user_message(question)
        history.add_ai_message(answer)
        return AnswerResult(
            answer=answer,
            provider=generation.provider,
            category_hint=category_hint,
            response_mode="generated",
            used_fallback=generation.provider != "openai",
            rewritten_question=rewritten_question,
            retrieved_docs=[item.document for item in retrieved_docs[:3]],
            provider_errors=generation.errors,
        )
    except AllProvidersFailedError as exc:
        history.add_user_message(question)
        history.add_ai_message(copy["busy"])
        return AnswerResult(
            answer=copy["busy"],
            provider="fallback_error",
            category_hint=category_hint,
            response_mode="busy",
            used_fallback=True,
            rewritten_question=rewritten_question,
            retrieved_docs=[item.document for item in retrieved_docs[:3]],
            provider_errors=exc.errors,
        )
