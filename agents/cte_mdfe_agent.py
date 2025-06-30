from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from vector_utils import get_retriever, rerank_docs

def cte_mdfe_agent(state: dict) -> dict:
    pergunta = state["pergunta"]

    retriever = get_retriever(filtro="CTE_MDFE")
    docs = retriever.invoke(pergunta)
    docs = rerank_docs(pergunta, docs, top_k=5)
    contexto = "\n".join(d.page_content for d in docs) if docs else ""

    print("\n=== [CTE/MDFE] Chunks recuperados individualmente ===")
    for i, d in enumerate(docs, 1):
        print(f"Doc {i}:\n{d.page_content}\n")

    #contexto = "\n".join(d.page_content for d in docs)

    print("\n=== [CTE/MDFE] Texto total passado para IA ===")
    print(contexto)
    print("===================================================\n")

    prompt = ChatPromptTemplate.from_template(
    """
DOCUMENTOS DE REFERÊNCIA:
=========================
{docs}

PERGUNTA DO USUÁRIO:
====================
{pergunta}

INSTRUÇÕES:
- Utilize apenas as informações dos documentos.
- Se não encontrar a resposta, diga: "Desculpe, não encontrei essa informação nos documentos disponíveis."
- Use listas ou tópicos sempre que possível. Emojis são permitidos com moderação.

NUNCA inclua frases como “se não encontrou nos documentos, diga...”.
O usuário final não deve ver instruções internas, apenas a resposta direta à pergunta.
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
