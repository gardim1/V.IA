from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("""
Classifique a pergunta abaixo em UMA das categorias:
CTE_MDFE, ROTEIRIZACAO, RELATORIOS, DEVOLUCAO,
CHAMADOS, TRANSPORTADORA, FROTA, INDENIZACAO, GERAL.

Responda APENAS com o nome exato da categoria, sem explicações.

Pergunta: {pergunta}
Categoria:
""")

model = OllamaLLM(model="mistral:7b")  

chain = prompt | model

def roteador_tool(state: dict) -> dict:
    categoria = chain.invoke({"pergunta": state["pergunta"]}).strip().upper()

    validas = {
        "CTE_MDFE", "ROTEIRIZACAO", "RELATORIOS", "DEVOLUCAO",
        "CHAMADOS", "TRANSPORTADORA", "FROTA", "INDENIZACAO", "GERAL"
    }
    if categoria not in validas:
        categoria = "GERAL"

    return {"next": categoria.lower()}
