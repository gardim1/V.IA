from agents.templates import prompt
from llm_provider import get_rag_primary_llm, get_rag_local_llm
from vector_utils import get_retriever, rerank_docs
from utils.history_chain import wrap_with_history

RESPOSTA_SEM_DOCS = "Desculpe, não encontrei essa informação nos documentos disponíveis."
RESPOSTA_ERRO = "Desculpe, não consegui processar sua pergunta no momento."

def run_rag_agent(state: dict, categoria: str, nome_log: str) -> dict:
    pergunta = state["pergunta"]
    user_id = state.get("user_id")

    if not user_id:
        raise ValueError("user_id está ausente ou é None")

    try:
        retriever = get_retriever(categoria)
        docs = retriever.invoke(pergunta)
        docs = rerank_docs(pergunta, docs, top_k=3)
        contexto = "\n".join(d.page_content for d in docs) if docs else ""
    except Exception as e:
        print(f"Erro no retrieval [{nome_log}]: {e}")
        docs = []
        contexto = ""

    if docs:
        print(f"\n=== [{nome_log}] Chunks recuperados individualmente ===")
        for i, d in enumerate(docs, 1):
            print(f"Doc {i}:\n{d.page_content}\n")

        print(f"\n=== [{nome_log}] Texto total passado para IA ===")
        print(contexto)
        print("===================================================\n")

    if not docs:
        return {
            "pergunta": pergunta,
            "resposta": RESPOSTA_SEM_DOCS,
            "next": "",
            "user_id": user_id
        }

    try:
        pipeline = prompt | get_rag_primary_llm()
        chain = wrap_with_history(pipeline, user_id)

        resposta = chain.invoke(
            {"docs": contexto, "pergunta": pergunta},
            config={"configurable": {"session_id": user_id}}
        )

        if hasattr(resposta, "content"):
            resposta = resposta.content

        if not isinstance(resposta, str):
            resposta = str(resposta)

    except Exception as e:
        print(f"Erro no provider principal [{nome_log}]: {e}")
        print(f"[FALLBACK] Tentando Ollama local em [{nome_log}]...")

        try:
            pipeline = prompt | get_rag_local_llm()
            chain = wrap_with_history(pipeline, user_id)

            resposta = chain.invoke(
                {"docs": contexto, "pergunta": pergunta},
                config={"configurable": {"session_id": user_id}}
            )

            if hasattr(resposta, "content"):
                resposta = resposta.content

            if not isinstance(resposta, str):
                resposta = str(resposta)
        except Exception as e2:
            print(f"Erro no fallback local [{nome_log}]: {e2}")
            resposta = RESPOSTA_ERRO

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": "",
        "user_id": user_id
    }