from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import traceback

router = APIRouter()
model = OllamaLLM(model="llama3.2:latest")

prompt = ChatPromptTemplate.from_template("""
Você é o REVISOR-FINAL da LIA, assistente dos cleintes da Sislogica que usam o TMS.

Contexto:
• Pergunta anterior: {pergunta_anterior}
• Pergunta atual:   {pergunta_atual}
• Documentos recuperados (fonte de verdade): {dados_retrieved}
• Resposta gerada:  {resposta_gerada}

Tarefa em 3 passos curtos
1. Verifique se {dados_retrieved} contém informação suficiente para responder {pergunta_atual}.
2. Se SIM, escreva a resposta usando **somente** o que estiver explícito em {dados_retrieved}.  
   – Remova qualquer frase de desconhecimento (“não sei”, “não encontrei”).  
   – Corrija contradições; mantenha partes que já estão corretas.
3. Se NÃO, responda exatamente:  
   > Desculpe, não encontrei essa informação nos documentos pesquisados.

Regras finais
• Não invente nem especule.  
• Não adicione prefixos ou notas como “Resposta revisada:”.  
• A resposta deve ser clara, objetiva e profissional, em português brasileiro. Pode usar emojis para melhorar a experiência do usuário, mas evite excessos.

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
