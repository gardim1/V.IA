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

- Se a resposta está **coerente com os dados fornecidos**.  
- Se não há **informações faltantes** que estão nos dados.  
- Se não há **informações incorretas** ou **contradições internas**.  
- Se a resposta **não responde de forma contraditória** (ex: primeiro diz que sabe, depois diz que não sabe).  
- Se a resposta está **bem estruturada e objetiva**.

Regras IMPORTANTES:

- Você deve considerar os `dados_retrieved` como a fonte de verdade.  
- Se a resposta anterior disser que "não sabe" algo, mas os dados contêm essa informação, você deve corrigir isso.  
- Se a resposta anterior tiver um começo certo e um final errado, você deve MANTER o certo e corrigir o errado.  
- Se os dados não contiverem a resposta, você deve dizer que não sabe — mesmo que a resposta anterior tenha inventado.  

Retorne apenas a resposta final e aprimorada. NÃO repita os erros da resposta original. NÃO hesite em corrigir. Reponda APENAS a resposta revisada, sem explicações adicionais ou contextos.

Elementos:

- Pergunta anterior: {pergunta_anterior}  
- Pergunta atual: {pergunta_atual}  
- Dados recuperados: {dados_retrieved}  
- Resposta da IA: {resposta_gerada}

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
