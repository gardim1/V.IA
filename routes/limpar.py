import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from utils.history import clear_history

load_dotenv()

router = APIRouter()


@router.delete(
    "/history/{user_id}",
    tags=["Deletar Historico"],
    summary="Deletar historico de mensagens",
)
async def delete_history(user_id: str):
    if os.getenv("ENV", "dev") != "dev":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    result = clear_history(user_id)
    return {"status": "ok", **result}
