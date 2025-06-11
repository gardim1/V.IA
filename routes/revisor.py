from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

import traceback

router = APIRouter()

model = OllamaLLM(model="llama3.2:latest")

class RevisaoResposta(BaseModel):
    pergunta_anterior: str
    pergunta_atual: str
    dados_retrieved: str
    resposta_gerada: str

@router.post("/revisar_resposta", tags=["IA LIA"], response_model=dict)
async def revisar_resposta(dados: RevisaoResposta):
    try:
        prompt_template = """
Você é um revisor especializado em garantir a qualidade de respostas de uma IA do sistema TMS.

Sua tarefa é analisar a resposta gerada pela IA e verificar:

✅ Se a resposta está **coerente** com as informações dos dados fornecidos.  
✅ Se não há **informações faltantes** que estão nos dados.  
✅ Se não há **informações repetidas** ou **redundantes**.  
✅ Se a resposta **não responde a mesma pergunta mais de uma vez**.  
✅ Se a resposta está **bem estruturada e objetiva**.

Se a resposta estiver boa → apenas reescreva a mesma resposta no campo "Resposta Revisada", com possíveis pequenas melhorias de clareza.

Se houver problemas → reescreva a resposta corrigida, eliminando repetições, adicionando informações que faltavam, e melhorando a estrutura.

Use os seguintes elementos:

- Pergunta anterior do cliente: {pergunta_anterior}
- Pergunta atual do cliente: {pergunta_atual}
- Documentos recuperados pelo banco vetorial: {dados_retrieved}
- Resposta gerada pela IA: {resposta_gerada}

Retorne apenas o campo "Resposta Revisada", com a resposta final e aprimorada. Não escreva explicações adicionais, apenas a resposta final para o cliente.
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | model

        resposta_revisada = chain.invoke({
            "pergunta_anterior": dados.pergunta_anterior,
            "pergunta_atual": dados.pergunta_atual,
            "dados_retrieved": dados.dados_retrieved,
            "resposta_gerada": dados.resposta_gerada
        })

        return {"resposta_revisada": resposta_revisada}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
