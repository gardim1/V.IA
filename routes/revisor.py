from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import traceback

router = APIRouter()
model = OllamaLLM(model="llama3.2:latest")

prompt = ChatPromptTemplate.from_template("""
Você é um revisor responsável por garantir a qualidade de respostas de uma IA sobre o sistema TMS da Sislogica.

1. Leia:
• Pergunta anterior: {pergunta_anterior}
• Pergunta atual: {pergunta_atual}
• Dados recuperados: {dados_retrieved}
• Resposta gerada: {resposta_gerada}

2. Gere apenas a resposta final revisada seguindo:
• Use exclusivamente {dados_retrieved}.
• Não invente nada.
• Não adicione prefixos.
• Corrija contradições e mantenha partes corretas.
• Diga que não sabe apenas se a informação não existir nos dados.
• Responda em português brasileiro.
""")

revisor_chain = prompt | model

class RevisaoResposta(BaseModel):
    pergunta_anterior: str
    pergunta_atual: str
    dados_retrieved: str
    resposta_gerada: str

@router.post("/revisar_resposta", tags=["IA LIA"], response_model=dict)
async def revisar_resposta(dados: RevisaoResposta):
    try:
        resposta = revisor_chain.invoke(dados.model_dump())
        return {"resposta_revisada": resposta}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
