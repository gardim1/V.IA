from fastapi import APIRouter

router = APIRouter()

@router.get("/status",
            summary="Healthcheck",
            description="Verifica se a API está ativa e recebendo requisicoes",
            tags=["Status"])
def healthcheck():
    return {"status": "ok"}
