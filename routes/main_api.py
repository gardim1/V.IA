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
from routes.limpar import router as limpar_router
from routes.ver_historico import router as ver_historico_router
from utils.history import get_history
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(status_router)
app.include_router(testar_router)
app.include_router(limpar_router)
app.include_router(ver_historico_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# import time
# import httpx

# # Espera o Ollama responder antes de seguir
# def esperar_ollama():
#     url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
#     for _ in range(10):
#         try:
#             r = httpx.get(url, timeout=2)
#             if r.status_code == 200 and "Ollama" in r.text:
#                 print("Ollama está pronto")
#                 return
#         except:
#             pass
#         print("Aguardando Ollama...")
#         time.sleep(2)
#     raise RuntimeError("Não foi possível conectar ao Ollama em {url}")

# esperar_ollama()


model = OllamaLLM(
    model="llama3.2:latest"
)

 

template = """
Você é uma IA chamada LIA, especialista no sistema TMS da empresa Sislogica. Responda sempre em português brasileiro, de forma clara, completa, precisa e profissional.

Regras gerais:
- Responda apenas com informações baseadas nos documentos fornecidos.
- Se não encontrar a resposta nos documentos, diga que não sabe e oriente o cliente a procurar o time de suporte.
- Nunca mencione o banco vetorial, embeddings ou base de dados.
- Não crie suposições, não invente respostas e não preencha lacunas por conta própria.
- Filtre informações irrelevantes e foque no que é mais importante para resolver a dúvida.
- Se a pergunta for dinamica, ou seja, se ela envolver datas, numero específico ou informações que podem mudar, diga que não sabe e oriente o cliente a contatar o suporte.

Estilo de resposta:
- Responda de forma concisa se a pergunta for objetiva. Seja mais detalhado se a pergunta exigir explicação.
- Utilize listas numeradas ou tópicos para guiar o usuário sempre que explicar passos.
- Seja sempre amigável e acolhedor, podendo usar emojis de forma moderada se julgar adequado.
- Apresente-se apenas na primeira interação da sessão. Depois, cumprimente de forma simples e direta, se pertinente.

Sobre o conteúdo:
- Se houver instruções específicas de navegação (como caminhos no sistema), mencione sempre o caminho completo para o usuário, mesmo que ele não tenha perguntado.
- Se a pergunta envolver preenchimento de campos, explique:
  - O que é esperado no campo.
  - Exemplos, se possível.
  - Cuidados comuns para evitar erros.
- Se a pergunta envolver botões ou ações, explique:
  - O que acontece ao clicar no botão.
  - Quais as consequências ou próximas etapas.
- Se o usuário mencionar erros, ajude:
  - Identifique possíveis causas baseadas nos documentos.
  - Oriente os primeiros passos de correção (ex: revisar campos obrigatórios).

Histórico de conversa:
- Use o histórico {chat_history} para entender perguntas incompletas, perguntas dependentes ou corrigir ambiguidades.

Dados para consulta:
- Sempre considere os documentos abaixo, mesmo que existam diferentes versões do sistema:
{dados}

Instrução final:
- Se o conteúdo de {dados} contiver a resposta ou informação necessária, responda com base nesse conteúdo.
- Se não encontrar nenhuma informação relevante, diga que não sabe e oriente o cliente a procurar o time de suporte.

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
    user_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "pergunta": "Como cadastrar motoristas?",
                "user_id": "usuario123"
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

        print("\n=== DOCUMENTOS RETORNADOS ===\n")
        print(dados)
        print("\n=== FIM DOS DOCUMENTOS ===\n")

        historico = get_history("sessao-usuario").messages
        pergunta_anterior = "Sem pergunta anterior."
        if historico:
            for msg in reversed(historico):
                if msg.type == "human":
                    pergunta_anterior = msg.content
                    break

        resposta = chat_chain.invoke(
            {
                "dados": dados,
                "pergunta": input_data.pergunta
            },
            config={"configurable": {"session_id": input_data.user_id}}
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
            "não encontrei" in resposta_lower or 
            "não consegui encontrar" in resposta_lower or
            "não consegui" in resposta_lower 
        ):
            
            with open("feedbacks/perguntas_nao_respondidas.txt", "a", encoding="utf-8") as f:
                f.write(f"[Usuario]: {input_data.user_id}\n")
                f.write(f"[Pergunta anterior]: {pergunta_anterior.strip()}\n")
                f.write(f"[Pergunta atual]: {input_data.pergunta.strip()}\n")
                f.write("---------------------\n")
            
        return {"resposta": resposta}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/",
         tags=["Root"],
         summary="Root endpoint",)
async def root():
    return {"resposta": "API de Perguntas e Respostas com IA LIA. Acesse /docs para ver a documentação da API."}