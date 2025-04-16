from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.abspath("templates"))

@router.get("/testar", 
            summary="Interface de teste da LIA na web",
            description="Página HTML para testar a IA diretamente no navegador",
            tags=["Teste Web"],
            response_class=HTMLResponse
            )
async def testar(request: Request):
    return templates.TemplateResponse("test_interface.html", {"request": request})
