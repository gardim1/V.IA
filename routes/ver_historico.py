import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.get("/history/{user_id}",
            tags=["Histórico"],
            summary="Ver histórico de mensagens")
async def get_history(user_id: str):
    try:
        ttl= int(os.getenv("CHAT_TTL_SECONDS", 2592000))
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        history = RedisChatMessageHistory(
            session_id=user_id,
            url=redis_url,
            ttl=ttl
        )
        mensagens = history.messages
        historico_formatado = [{"autor": m.type, "mensagem": m.content} for m in mensagens]
        return {"historico": historico_formatado}
    except Exception as e:
        return {"error": str(e)}
