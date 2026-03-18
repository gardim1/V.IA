from functools import lru_cache

from fastapi import APIRouter
from keybert import KeyBERT
from stop_words import get_stop_words

from utils.history import get_history

router = APIRouter()
STOPWORDS_PT = get_stop_words("portuguese")


@lru_cache(maxsize=1)
def get_kw_model() -> KeyBERT:
    return KeyBERT(model="all-MiniLM-L6-v2")


def gerar_resumo_keybert(historico):
    textos = " ".join([message.content for message in historico if message.type == "human"])
    if not textos.strip():
        return "Nenhum historico relevante ainda."

    keywords = get_kw_model().extract_keywords(
        textos,
        keyphrase_ngram_range=(1, 2),
        stop_words=STOPWORDS_PT,
        top_n=5,
    )
    topicos = [keyword for keyword, _score in keywords]
    return f"Geralmente fala sobre: {', '.join(topicos)}."


@router.get("/usuario/{user_id}/resumo", tags=["IA Vinnie"])
async def obter_resumo_usuario(user_id: str):
    historico = get_history(user_id).messages
    resumo = gerar_resumo_keybert(historico)
    return {"user_id": user_id, "resumo": resumo}
