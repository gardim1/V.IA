from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

import traceback

router = APIRouter()

model = OllamaLLM(model="llama3.2:latest")

class FeedbackCompleto(BaseModel):
    pergunta_atual: str
    pergunta_anterior: str
    resposta_correta: str

@router.post("/formatar", tags=["IA LIA"], response_model=dict)
async def formatar_feedback_completo(dados: FeedbackCompleto):
    try:
        prompt_template = """
Você é um especialista técnico encarregado de transformar respostas soltas em instruções bem formatadas e claras.

Sua tarefa é gerar uma resposta técnica e bem estruturada no seguinte formato:

===== TÍTULO =====
Caminho: ...
Como realizar: ...
Campos: ...
Observações: ...

Use as informações abaixo:

- Pergunta anterior do cliente: {pergunta_anterior}
- Pergunta atual do cliente: {pergunta_atual}
- Resposta correta a ser formatada: {resposta_correta}

Evite repetir perguntas. Dê um título claro, extraia o caminho se houver, explique de forma passo a passo como realizar, detalhe os campos envolvidos e adicione observações úteis.

Responda apenas com o texto já formatado.
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | model

        resposta = chain.invoke({
            "pergunta_anterior": dados.pergunta_anterior,
            "pergunta_atual": dados.pergunta_atual,
            "resposta_correta": dados.resposta_correta
        })

        return {"resposta": resposta}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
