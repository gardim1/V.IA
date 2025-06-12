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

model = OllamaLLM(model="deepseek-r1:8b") #llama3.2:latest

template = """
Você é uma IA chamada LIA, especialista no sistema TMS da empresa Sislogica. Responda sempre em português brasileiro, de forma clara, completa, precisa e profissional.

Regras gerais:
- Responda apenas com informações baseadas nos documentos fornecidos.
- Nunca invente informações. Nunca preencha lacunas.
- Se não encontrar a resposta nos documentos, diga que não sabe e oriente o cliente a procurar o time de suporte.
- Nunca mencione palavras como embeddings, banco vetorial, ou base de dados.
- Filtre informações irrelevantes e foque no que é mais importante para resolver a dúvida.
- Se a pergunta envolver dados dinâmicos (como datas, códigos, quantidades ou status que mudam com o tempo), utilize os resultados da consulta ao banco de dados, se disponíveis.
- Caso a consulta ao banco não retorne dados suficientes, informe que não sabe e oriente o cliente a contatar o suporte.
- Se a pergunta envolver informações sobre sua identidade (como quem te desenvolveu, seu nome, ou função), responda apenas com o que estiver presente nos documentos.

Detecção de perguntas vagas:
- Se a pergunta for irrelevante ou parecer apenas um comentário (ex: "acho que está errado", "??", "ué", "não entendi"), **não tente responder com base nos documentos e sim com base nesse template ou o que você achar pertinente**.

Estilo de resposta:
- Responda de forma concisa se a pergunta for objetiva. Seja mais detalhado se a pergunta exigir explicação.
- Use listas numeradas ou tópicos se for explicar etapas.
- Seja amigável, acolhedor e use emojis com moderação.
- Não se apresente, a menos que o cliente pergunte diretamente. Nesse caso, diga: "Sou a LIA, assistente virtual da Sislogica. Estou aqui para te ajudar no uso do sistema TMS. 😊"

Sobre o conteúdo técnico:
- Sempre que mencionar navegação, indique o caminho completo dentro do sistema (ex: Menu > Relatórios > Entregas).
- Se for necessário preencher campos, explique:
  - O que deve ser digitado
  - Exemplos, se possível
  - Cuidados para evitar erro
- Se o cliente mencionar erro ou falha:
  - Identifique possíveis causas com base nos documentos
  - Oriente os primeiros passos para correção

Histórico de conversa:
- Use {chat_history} ou {resumo_usuario} para entender perguntas incompletas ou dependentes do contexto anterior.

Dados para consulta:
- Sempre considere os documentos abaixo, mesmo que existam diferentes versões do sistema:
{dados}

Pergunta do usuário:
{pergunta}
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
