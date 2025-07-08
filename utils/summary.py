from utils.history import get_history, redis_client
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

CHAVE_BASE = "resumo:"
BLOCO = 3

PROMPT = ChatPromptTemplate.from_template("""
Atualize o resumo do usuário em UMA frase.
Use o resumo_antigo (se existir) como base e inclua as novidades.

━━━━ RESUMO ANTIGO ━━━━
{resumo_antigo}

━━━━ BLOCO NOVO ━━━━
{historico_novo}

━━━━ RESUMO ATUALIZADO ━━━━
""")

LLM = OllamaLLM(model="mistral:7b")

def _uid(uid: str | None) -> str: 
    return uid or "anon"

def _key(uid: str) -> str:
    return CHAVE_BASE + uid

def _blocos_salvos(uid: str) -> int:
    val = redis_client.get(_key(uid) + ":cnt")
    return int(val) if val else 0

def _set_blocos(uid: str, n: int):
    redis_client.set(_key(uid) + ":cnt", n)

def _carregar(uid: str) -> str:
    val = redis_client.get(_key(uid))
    return val.decode("utf-8") if val else ""

def _salvar(uid: str, texto: str):
    redis_client.set(_key(uid), texto)

def ensure_resumo(user_id: str | None) -> str:
    uid = _uid(user_id)
    msgs = get_history(uid).messages
    blocos_atuais = len([m for m in msgs if m.type == "human"]) // BLOCO
    blocos_salvos  = _blocos_salvos(uid)

    if blocos_atuais == 0:
        return ""

    if blocos_atuais == blocos_salvos:
        return _carregar(uid)

    inicio = blocos_salvos * BLOCO
    historico_novo = "\n".join(
        f"{'Usuário' if m.type=='human' else 'LIA'}: {m.content}"
        for m in msgs[inicio : inicio + BLOCO]
    )

    resumo_antigo = _carregar(uid)

    novo_resumo = (
        PROMPT | LLM
    ).invoke(
        {"resumo_antigo": resumo_antigo, "historico_novo": historico_novo}
    ).strip()

    _salvar(uid, novo_resumo)
    _set_blocos(uid, blocos_atuais)
    return novo_resumo
