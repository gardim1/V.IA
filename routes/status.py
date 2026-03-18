from fastapi import APIRouter

from llm_provider import get_local_generation_health, get_ollama_server_health, get_openai_health
from utils.history import get_redis_health
from vector_utils import get_vector_store_health

router = APIRouter()


@router.get(
    "/status",
    summary="Healthcheck",
    description="Verifica se a API esta ativa e mostra o estado rapido das dependencias",
    tags=["Status"],
)
def healthcheck():
    return {
        "status": "ok",
        "checks": {
            "openai": get_openai_health(probe=False),
            "ollama": get_ollama_server_health(),
            "redis": get_redis_health(),
            "chroma": get_vector_store_health(),
        },
    }


@router.get("/status/openai", tags=["Status"], summary="Probe da OpenAI")
def healthcheck_openai():
    return get_openai_health(probe=True)


@router.get("/status/local", tags=["Status"], summary="Probe do provider local")
def healthcheck_local():
    return get_local_generation_health()


@router.get("/status/redis", tags=["Status"], summary="Probe do Redis")
def healthcheck_redis():
    return get_redis_health()


@router.get("/status/vector", tags=["Status"], summary="Probe do Chroma")
def healthcheck_vector():
    return get_vector_store_health()
