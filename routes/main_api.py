import sys
import os
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

model = OllamaLLM(model="llama3.2")

template = """
Você é uma IA chamada LIA, especialista no sistema TMS da empresa Sislogica. Responda sempre em português brasileiro, de forma clara, completa e profissional.

Se não encontrar a resposta nos documentos fornecidos, diga que não sabe e oriente o cliente a procurar o time de suporte. Você pode dizer "Não sei a resposta para essa pergunta" no meio de sua resposta. **Nunca mencione o banco vetorial**. 

Não faça suposições ou crie informações. Se não souber a resposta, diga que não sabe e oriente o cliente a procurar o time de suporte.

Não responda mais do que for necessário. Evite ser prolixo ou repetir informações.

NAO INVENTE INFORMACAO RESPONDA APENAS O QUE ETSA NO BANCO DE DADOS VETORIAL. NAO USE RACIOCINIO E NAO FAÇA SUPOSIÇÕES. SE NAO ENCONTRAR A RESPOSTA NOS DOCUMENTOS FORNECIDOS, DIGA QUE NAO SABE E ORIENTE O CLIENTE A PROCURAR O TIME DE SUPORTE.

Apresente-se apenas na primeira resposta da sessão. Em outras interações, use saudações amigáveis se for pertinente.

Há um arquivo que diz o caminho para acessar cada página do sistema. Sempre mencione o caminho correto para acessar a página, mesmo que o usuário não pergunte. Lembre-se de esclarecer a duvida de forma completa, quais campos preencher e como preencher.

Se o usuário perguntar sobre um campo específico, explique como preencher esse campo e quais informações são necessárias. Se o usuário perguntar sobre um botão específico, explique o que acontece quando ele clica nesse botão e quais ações ele pode realizar.

Se você já respondeu corretamente a pergunta, **NAO FINALIZE DIZENDO QUE NAO SABE A RESPOSTA**.

Utilize o histórico da conversa para entender perguntas incompletas ou com dependência de contexto:
{chat_history}

Sempre considere as informações dos documentos abaixo, mesmo que existam diferentes versões do sistema:
{dados}

Pergunta do usuário:
{pergunta}
"""

#fazer o Ollama ver sua propria resposta e usa-la pra verificar se a pergunta está boa e/ou bem formatada.

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
        json_schema_extra = {
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

        resposta_lower = resposta.lower()
        if(
            "não sei a resposta para essa pergunta" in resposta_lower or
            "não tenho certeza" in resposta_lower or
            "não sei" in resposta_lower or
            "não posso ajudar" in resposta_lower or
            "não tenho essa informação" in resposta_lower or
            "não sei a resposta" in resposta_lower or
            "não tenho certeza sobre isso" in resposta_lower or
            "não posso responder isso" in resposta_lower or
            "não tenho certeza se posso ajudar com isso" in resposta_lower or
            "desculpe pela confusão anterior" in resposta_lower or
            "desculpe pela confusão" in resposta_lower or
            "desculpe, não tenho certeza" in resposta_lower or
            "não tenho certeza, mas" in resposta_lower or
            "não encontrei" in resposta_lower 
        ):
            with open("feedbacks/perguntas_nao_respondidas.txt", "a", encoding="utf-8") as f:
                f.write(input_data.pergunta.strip() + "\n")
            
        return {"resposta": resposta}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/",
         tags=["Root"],
         summary="Root endpoint",)
async def root():
    return {"resposta": "API de Perguntas e Respostas com IA LIA. Acesse /docs para ver a documentação da API."}