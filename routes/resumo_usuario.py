from fastapi import APIRouter
from utils.history import get_history
from keybert import KeyBERT
from stop_words import get_stop_words

router = APIRouter()

kw_model = KeyBERT(model="all-MiniLM-L6-v2")
STOPWORDS_PT = get_stop_words("portuguese")            

def gerar_resumo_keybert(historico):
    textos = " ".join([msg.content for msg in historico if msg.type == "human"])
    if not textos.strip():
        return "Nenhum histórico relevante ainda."

    keywords = kw_model.extract_keywords(
        textos,
        keyphrase_ngram_range=(1, 2),
        stop_words=STOPWORDS_PT,   
        top_n=5
    )
    topicos = [kw for kw, _ in keywords]
    return f"Geralmente fala sobre: {', '.join(topicos)}."

@router.get("/usuario/{user_id}/resumo", tags=["IA LIA"])
async def obter_resumo_usuario(user_id: str):
    historico = get_history(user_id).messages
    resumo = gerar_resumo_keybert(historico)
    return {"user_id": user_id, "resumo": resumo}
