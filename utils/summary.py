from utils import get_history, redis_client
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

CHAVE_PADRAO = "resumo:"

def resumo_ja_gerado(user_id: str) -> bool:
    return redis_client.exists(CHAVE_PADRAO + user_id) ==1

def salvar_resumo(user_id: str, texto: str) -> None:
    redis_client.set(CHAVE_PADRAO + user_id, texto)

def carregar_resumo(user_id: str) -> str:
    val = redis_client.get(CHAVE_PADRAO + user_id)
    return val.decode("utf-8") if val else ""

def gerar_resumo_via_llm(user_id: str) -> str:
    historico = get_history(user_id).messages
    if len(historico) < 3:
        return ""
    
    linhas = []

    for msg in historico:
        quem = "Usuário" if msg.type == "human" else "LIA"
        linhas.append(f"{quem}: {msg.content}")

    prompt = ChatPromptTemplate.from_template(
        """
Resuma, em uma frase curta, as informações importantes sobre o usuário:
nome (se informado), interesses ou temas recorrentes, tom geral.

Histórico:
{conversa}

Resumo:
"""
    )

    llm = OllamaLLM(model="mistral:7b")
    resumo = (prompt | llm).invoke({"conversa": "\n".join(linhas).strip()})

    salvar_resumo(user_id, resumo)
    return resumo