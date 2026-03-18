from fastapi import APIRouter

from utils.history import get_history

router = APIRouter()


@router.get(
    "/history/{user_id}",
    tags=["Historico"],
    summary="Ver historico de mensagens",
)
async def get_history_route(user_id: str):
    try:
        history = get_history(user_id)
        mensagens = history.messages
        historico_formatado = [{"autor": message.type, "mensagem": message.content} for message in mensagens]
        return {"backend": history.backend, "historico": historico_formatado}
    except Exception as exc:
        return {"error": str(exc)}
