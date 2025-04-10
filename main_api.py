from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = Ollama(model="llama3.2")

template = """
Você é uma IA especialista no sistema TMS da empresa Sislogica. Você deve responder todas as perguntas do usuário de forma completa, clara e profissional. Se a pergunta não existir no banco vetorial, diga explicitamente que você não sabe e oriente o cliente a procurar ajuda com o time de suporte. Você DEVE responder tudo em português brasileiro.

Aqui estão os documentos do banco vetorial: {dados}

Aqui está a pergunta para responder: {pergunta}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

class Pergunta(BaseModel):
    pergunta: str

@app.post("/perguntar")
async def perguntar(input_data: Pergunta):
    try:
        retriever = get_retriever()
        dados = retriever.invoke(input_data.pergunta)
        resultado = chain.invoke({"dados": dados, "pergunta": input_data.pergunta})
        return {"resposta": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

