from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever

def roteirizacao_agent(state: dict) -> str:
    pergunta = state["pergunta"]
    retriever = get_retriever(filtro="ROTEIRIZACAO")
    docs = retriever.invoke(pergunta)
    contexto = "\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_template(
        "Responda com base nos documentos abaixo:\n\n{docs}\n\nPergunta: {pergunta}"
    )
    model = OllamaLLM(model="llama3.2:latest")
    chain = prompt | model
    return chain.invoke({"docs": contexto, "pergunta": pergunta})
