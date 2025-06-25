from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever

def roteirizacao_agent(state: dict) -> dict:
    pergunta = state["pergunta"]

    retriever = get_retriever(filtro="ROTEIRIZACAO")
    docs = retriever.invoke(pergunta)
    contexto = "\n".join(d.page_content for d in docs) if docs else ""

    prompt = ChatPromptTemplate.from_template(
        "Responda com base nos documentos abaixo:\n\n{docs}\n\nPergunta: {pergunta}"
    )
    resposta = (prompt | OllamaLLM(model="llama3.2:latest")).invoke(
        {"docs": contexto, "pergunta": pergunta}
    )

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": ""
    }
