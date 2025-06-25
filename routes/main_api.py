import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
os.makedirs("feedbacks", exist_ok=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from routes.status import router as status_router
from routes.testar import router as testar_router
from routes.limpar import router as limpar_router
from routes.ver_historico import router as ver_historico_router
from utils.history import get_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from dotenv import load_dotenv
from datetime import datetime
import re
from typing import Dict, List
from keybert import KeyBERT
from stop_words import get_stop_words
from routes.resumo_usuario import router as resumo_router, gerar_resumo_keybert
from routes.formatar import router as formatador_router
from routes.revisor import router as revisor_router
from routes.revisor import revisor_chain

load_dotenv()

app = FastAPI()
app.include_router(status_router)
app.include_router(testar_router)
app.include_router(limpar_router)
app.include_router(ver_historico_router)
app.include_router(resumo_router)
app.include_router(formatador_router)
app.include_router(revisor_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = OllamaLLM(model="llama3.2:latest") #llama3.2:latest #deepseek-r1:8b

template = """
Você é a **LIA**, assistente virtual da Sislogica especializada no sistema TMS.  
Responda sempre em **português brasileiro**, de forma clara, completa, precisa e profissional.

━━━━━━━━  INSTRUÇÕES ABSOLUTAS  ━━━━━━━━
1. Use **exclusivamente** as informações contidas nos documentos abaixo ({dados}).  
2. **NUNCA** invente dados, preencha lacunas ou faça suposições.  
3. Se a informação solicitada **não estiver** nos documentos ou não puder ser inferida diretamente, responda exatamente:  
   > Desculpe, não encontrei essa informação nos documentos pesquisados.  
4. Perguntas totalmente fora do escopo Sislogica / TMS / LIA (ex.: futebol, celebridades) ⇒ mesma resposta-padrão acima.  
5. Não mencione termos como “embeddings”, “base vetorial”, “banco de dados” ou processos internos.  
6. Perguntas vagas/irrelevantes (ex.: “??”, “ué”, “não entendi”) ⇒ responda:  
   > Compreendo. Por favor, especifique melhor sua dúvida para que eu possa ajudar.  
7. Caso a pergunta seja dinâmica (dados que mudam) e os documentos não tragam a resposta atual, use a resposta-padrão do item 3.

━━━━━━━━  ESTILO  ━━━━━━━━
• Seja conciso para perguntas objetivas; detalhado quando necessário.  
• Use listas numeradas ou tópicos para etapas.  
• Emojis são permitidos com moderação.  
• Apresente-se apenas na primeira interação da sessão.

━━━━━━━━  CONTEXTO ADICIONAL  ━━━━━━━━
Histórico: {chat_history}  
Resumo do usuário: {resumo_usuario}

━━━━━━━━  DOCUMENTOS (fonte de verdade)  ━━━━━━━━
{dados}

━━━━━━━━  PERGUNTA DO USUÁRIO  ━━━━━━━━
{pergunta}

━━━━━━━━  SAÍDA  ━━━━━━━━
Responda diretamente ao usuário, sem pensamentos internos, rótulos ou metadados.

"""

prompt = ChatPromptTemplate.from_template(template)

chat_chain = RunnableWithMessageHistory(
    runnable=prompt | model,
    get_session_history=get_history,
    input_messages_key="pergunta",
    history_messages_key="chat_history",
)

class Pergunta(BaseModel):
    pergunta: str
    user_id: str

    class Config:
        json_schema_extra = {
            "example": {"pergunta": "O relatório de rotas de 07/04/2024 foi processado?", "user_id": "u123"}
        }

@app.post("/perguntar", tags=["IA LIA"], response_model=dict)
async def perguntar(input_data: Pergunta):
    try:
        retriever = get_retriever()
        docs = retriever.invoke(input_data.pergunta)
        dados_retrieved = "\n".join([d.page_content for d in docs]) if docs else ""

        print("Documentos usados pra responder")
        print(dados_retrieved)

        if not dados_retrieved:
            raise HTTPException(status_code=404, detail="Nenhum documento encontrado.")

        historico = get_history(input_data.user_id).messages
        resumo_usuario = gerar_resumo_keybert(historico)

        pergunta_anterior = "Sem pergunta anterior."
        if historico:
            for msg in reversed(historico):
                if msg.type == "human":
                    pergunta_anterior = msg.content
                    break

        resposta = chat_chain.invoke(
            {
                "dados": dados_retrieved,
                "pergunta": input_data.pergunta,
                "resumo_usuario": resumo_usuario,
            },
            config={"configurable": {"session_id": input_data.user_id}},
        )

        resposta_lower = resposta.lower()
        if (
            "não sei a resposta para essa pergunta" in resposta_lower
            or "não tenho certeza" in resposta_lower
            or "não sei" in resposta_lower
            or "não posso ajudar" in resposta_lower
            or "não tenho essa informação" in resposta_lower
            or "não sei a resposta" in resposta_lower
            or "não tenho certeza sobre isso" in resposta_lower
            or "não posso responder isso" in resposta_lower
            or "não tenho certeza se posso ajudar com isso" in resposta_lower
            or "desculpe pela confusão anterior" in resposta_lower
            or "desculpe pela confusão" in resposta_lower
            or "desculpe, não tenho certeza" in resposta_lower
            or "não tenho certeza, mas" in resposta_lower
            or "não encontrei" in resposta_lower
            or "não consegui encontrar" in resposta_lower
            or "não consegui" in resposta_lower
        ):
            with open("feedbacks/feedbacks.txt", "a", encoding="utf-8") as f:
                f.write(f"[Usuario]: {input_data.user_id}\n")
                f.write(f"[Pergunta anterior]: {pergunta_anterior.strip()}\n")
                f.write(f"[Pergunta atual]: {input_data.pergunta.strip()}\n")
                f.write("=========================================================================\n")

        payload = {
            "pergunta_anterior": pergunta_anterior,
            "pergunta_atual":   input_data.pergunta,
            "dados_retrieved":  dados_retrieved,
            "resposta_gerada":  resposta,
        }

        try:
            resposta_revisada = revisor_chain.invoke(payload)
        except Exception as e:
            print("Erro ao revisar resposta:", str(e))
            resposta_revisada = resposta

        return {"resposta": resposta_revisada}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"resposta": "API de Perguntas e Respostas com IA LIA. Acesse /docs."}
