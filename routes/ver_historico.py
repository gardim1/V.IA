from langchain_community.chat_message_histories import RedisChatMessageHistory
from fastapi import APIRouter

router = APIRouter()

@router.get("/history/{user_id}",
            tags=["Histórico"],
            summary="Ver histórico de mensagens")
async def get_history(user_id: str):
    try:
        history = RedisChatMessageHistory(
            session_id=user_id,
            url="redis://localhost:6379"
        )
        mensagens = history.messages
        historico_formatado = [{"autor": m.type, "mensagem": m.content} for m in mensagens]
        return {"historico": historico_formatado}
    except Exception as e:
        return {"error": str(e)}
