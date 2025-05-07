import redis
import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

print("ENV ATUAL:", os.getenv("ENV"))

router = APIRouter() 

@router.delete("/history/{user_id}",
               tags=["Deletar Histórico"],
               summary="Deletar histórico de mensagens")
async def delete_history(user_id: str):

    try:
        if os.getenv("ENV", "dev") != "dev":
            raise HTTPException(status_code=403, detail="Acesso negado.")
        r = redis.from_url("redis://localhost:6379")

        todas_chaves = r.keys("*")
        print("=== CHAVES NO REDIS ===")
        for k in todas_chaves:
            print(k)

        chave = f"message_store:{user_id}"
        deleted = r.delete(chave)
        print(f"Tentando deletar chave: {chave} → deletado? {deleted}")

        return {"status": "ok", "deleted": bool(deleted)}
    except redis.ConnectionError:
        raise HTTPException(status_code=500, detail="Não foi possível conectar ao Redis local.")
