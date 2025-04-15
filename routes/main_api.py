import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from routes.status import router as status_router
from routes.testar import router as testar_router
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory


session_history = {}

def get_history(session_id):
    if session_id not in session_history:
        session_history[session_id] = InMemoryChatMessageHistory()
    return session_history[session_id]

app = FastAPI()

app.include_router(status_router)
app.include_router(testar_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = Ollama(model="llama3.2")

template = """
Você é uma IA especialista no sistema TMS da empresa Sislogica. Seu nome é LIA. Você deve responder todas as perguntas do usuário de forma completa, clara e profissional. Se a pergunta não existir no banco vetorial, diga explicitamente que você não sabe e oriente o cliente a procurar ajuda com o time de suporte. Você não precisa falar sobre seu banco vetorial para o cliente. Você DEVE responder tudo em português brasileiro.

Aqui está o histórico da conversa. Use esse histórico para entender perguntas que estejam incompletas ou dependam de contexto anterior:{chat_history}

Mesmo se existirem diversas versões do TMS, responda o que está no banco de dados vetorial.
Exemplo: "Como cadastrar motoristas?"
Após sua resposta, se o cliente perguntar por exemplo:
"E veiculos?", você deve responder como se a pergunta fosse "Como cadastrar veiculos?"

Aqui estão os documentos do banco vetorial: {dados}

Aqui está a pergunta para responder: {pergunta}

"""

prompt = ChatPromptTemplate.from_template(template)

chat_chain = RunnableWithMessageHistory(
    runnable=prompt | model,
    get_session_history=get_history,
    input_messages_key="pergunta",
    history_messages_key="chat_history"
)

class Pergunta(BaseModel):
    pergunta: str

    class Config:
        schema_extra = {
            "example": {
                "pergunta": "Como cadastrar motoristas?"
            }
        }

@app.post("/perguntar",
          summary = "Enviar pergunta para a IA LIA",
          description = "Enviar uma pergunta para a IA LIA e receber uma resposta com base no banco de dados vetorial.",
          response_model=dict,
          tags=["IA LIA"])
async def perguntar(input_data: Pergunta):
    try:
        retriever = get_retriever()

        docs = retriever.invoke(input_data.pergunta)
        dados = "\n".join([doc.page_content for doc in docs]) if docs else "Nenhum conteúdo relevante encontrado."

        resposta = chat_chain.invoke(
            {
                "dados": dados,
                "pergunta": input_data.pergunta
            },
            config={"configurable": {"session_id": "sessao-usuario"}}
        )

        return {"resposta": resposta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
