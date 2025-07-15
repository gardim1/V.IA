from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever, rerank_docs
from utils.history_chain import wrap_with_history
from agents.templates import prompt

def frota_agent(state: dict) -> dict:
    pergunta = state["pergunta"]
    user_id = state.get("user_id")
    if not user_id:
        raise ValueError("user_id está ausente ou é None")

    try:
        retriever = get_retriever(filtro="FROTA")
        docs = retriever.invoke(pergunta)
        docs = rerank_docs(pergunta, docs, top_k=1)
    except Exception as e:
        print(f"Erro no retrieval: {e}")
        docs = []

    contexto_valido = bool(docs)
    #contexto = ""
    
    if docs:
        print("\n=== [FROTA] Chunks recuperados individualmente ===")
        for i, d in enumerate(docs, 1):
            print(f"Doc {i}:\n{d.page_content}\n")
            if len(d.page_content.strip()) > 50:
                contexto_valido = True
        
        contexto = "\n".join(d.page_content for d in docs)
        print("\n=== [FROTA] Texto total passado para IA ===")
        print(contexto)
        print("===================================================\n")
    
    if not contexto_valido:
        resposta_padrao = (
            "Desculpe, não encontrei informações suficientes para responder sua pergunta sobre frotas. "
            "Por favor entre em contato com o suporte da Sislogica por meio do:\n"
            "📱 WhatsApp: +55 11 97053-1979\n"
            "✉️ Email: suporte@sislogica.com.br"
        )
        return {
            "pergunta": pergunta,
            "resposta": resposta_padrao,
            "next": "",
            "user_id": user_id
        }
    
    try:
        pipeline = prompt | OllamaLLM(model="mistral:7b", temperature=0.3)
        chain = wrap_with_history(pipeline, user_id)

        resposta = chain.invoke(
            {"docs": contexto, "pergunta": pergunta},
            config={"configurable": {"session_id": user_id}}
        )
    except Exception as e:
        print(f"Erro na geração da resposta: {e}")
        resposta = (
            "Ocorreu um erro ao processar sua solicitação. "
            "Por favor entre em contato com o suporte técnico:\n"
            "📱 WhatsApp: +55 11 97053-1979"
        )

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": "",
        "user_id": user_id
    }