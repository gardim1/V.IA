from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import re

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

SMALL_TALK_PATTERNS = re.compile(
    r"^(oi|olá|ola|e[ai]\b|bom dia|boa tarde|boa noite|"
    r"tudo bem\??|como você está\??|qual.*seu nome|quem.*você|obrigado|obrigada)",
    re.I
)

def roteador_tool(state: dict) -> dict:
    pergunta = state["pergunta"].strip()

    if SMALL_TALK_PATTERNS.match(pergunta):
        categoria = "SMALL_TALK"
    else:
        categoria = chain.invoke({"pergunta": pergunta}).strip().upper()

    validas = {
        "SMALL_TALK",
        "CTE_MDFE", "ROTEIRIZACAO", "RELATORIOS", "DEVOLUCAO",
        "CHAMADOS", "TRANSPORTADORA", "FROTA", "INDENIZACAO", "GERAL"
    }
    if categoria not in validas:
        categoria = "GERAL"

    return {
        "pergunta": pergunta,
        "resposta": "",
        "next": categoria.lower()
    }
