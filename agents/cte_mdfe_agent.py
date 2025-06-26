from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from vector_utils import get_retriever, rerank_docs

def cte_mdfe_agent(state: dict) -> dict:
    pergunta = state["pergunta"]

    retriever = get_retriever(filtro="CTE_MDFE")
    docs = retriever.invoke(pergunta)
    docs = rerank_docs(pergunta, docs, top_k=3)
    contexto = "\n".join(d.page_content for d in docs) if docs else ""

    print("\n=== [CTE/MDFE] Documentos recuperados ===")
    for i, d in enumerate(docs, 1):
        print(f"Doc {i}:\n{d.page_content}\n")
    print("============================================\n")

    prompt = ChatPromptTemplate.from_template(
        """
Com base exclusivamente nos documentos abaixo, responda à pergunta do usuário de forma clara, objetiva e profissional:

{docs}

Pergunta: {pergunta}

 Instruções:
- Utilize apenas as informações presentes nos documentos.
- Estruture a resposta em tópicos ou passos sempre que possível.
- Use emojis com moderação para tornar a resposta amigável e leve, sem perder a formalidade.
- Se a resposta não estiver nos documentos, diga: "Desculpe, não encontrei essa informação nos documentos disponíveis."

"""
    )
    resposta = (prompt | OllamaLLM(model="llama3.2:latest")).invoke(
        {"docs": contexto, "pergunta": pergunta}
    )

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": ""         
    }
