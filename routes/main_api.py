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

load_dotenv()

app = FastAPI()
app.include_router(status_router)
app.include_router(testar_router)
app.include_router(limpar_router)
app.include_router(ver_historico_router)
app.include_router(resumo_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = OllamaLLM(model="llama3:8B")

template = """
Você é uma IA chamada LIA, especialista no sistema TMS da empresa Sislogica. Responda sempre em português brasileiro, de forma clara, completa, precisa e profissional.

Regras gerais:
- Responda apenas com informações baseadas nos documentos fornecidos.
- Se não encontrar a resposta nos documentos, diga que não sabe e oriente o cliente a procurar o time de suporte.
- Nunca mencione o banco vetorial, embeddings ou base de dados.
- Não crie suposições, não invente respostas e não preencha lacunas por conta própria.
- Filtre informações irrelevantes e foque no que é mais importante para resolver a dúvida.
- Se a pergunta envolver dados dinâmicos (como datas, códigos, quantidades ou status que mudam com o tempo), utilize os resultados da consulta ao banco de dados se eles estiverem disponíveis.
- Caso a consulta ao banco não retorne dados suficientes, diga que não sabe e oriente o cliente a contatar o suporte.
- Se a pergunta envolver informações sobre sua identidade (como quem te desenvolveu, qual é o seu nome, ou sua função), use as informações contidas nos documentos mesmo que estejam em formato de descrição ou metadados.


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
- Use o histórico {chat_history} ou {resumo_usuario} para entender perguntas incompletas, perguntas dependentes ou corrigir ambiguidades.

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

# def pergunta_dinamica(pergunta: str) -> bool:
#     padroes = [
#         r"\bj[aá] foi\b", r"\bfoi (entregue|processado|atualizado)\b",
#         r"\bfaltam\b", r"\bquantas?\b",
#         r"\bo relat[óo]rio (foi|est[áa])\b", r"\bj[aá] saiu\b",
#         r"\bconfirmar\b.*\b(entrega|processo|status)\b",
#         r"\bstatus\b.*\b(atual|entrega|pedido)\b",
#         r"\bentreg[ae]s? (pendentes|em aberto|atrasadas?)\b",
#     ]
#     return any(re.search(p, pergunta.lower()) for p in padroes)

# def extrair_parametros(pergunta: str) -> Dict[str, List[str]]:
#     params = {"datas": [], "termos": []}
#     params["datas"] = re.findall(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", pergunta)
#     termos = ["rotas", "relatório", "status", "entregas"]
#     params["termos"] = [t for t in termos if t in pergunta.lower()]
#     return params

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

        if not historico or all(not msg.content.strip() for msg in historico):
            pass
        else:
            pass

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
                "resumo_usuario": resumo_usuario          
            },
            config={"configurable": {"session_id": input_data.user_id}},
        )

        resposta_lower = resposta.lower()
        if (
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
            with open("feedbacks/feedbacks.txt", "a", encoding="utf-8") as f:
                f.write(f"[Usuario]: {input_data.user_id}\n")
                f.write(f"[Pergunta anterior]: {pergunta_anterior.strip()}\n")
                f.write(f"[Pergunta atual]: {input_data.pergunta.strip()}\n")
                f.write("=========================================================================\n")
                
        return {"resposta": resposta}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"resposta": "API de Perguntas e Respostas com IA LIA. Acesse /docs."}
