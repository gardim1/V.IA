from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="mistral:7b")

prompt = ChatPromptTemplate.from_template("""
Você é um classificador de perguntas de continuidade.

Considere duas perguntas: uma anterior e uma atual.  
Classifique se a **pergunta atual depende da anterior** para fazer sentido (ou seja, se é uma continuação da conversa).

Responda **apenas** com SIM ou NÃO.  
NÃO explique sua resposta.

----------------------
Pergunta anterior: {pergunta_anterior}

Pergunta atual: {pergunta_atual}
----------------------

A pergunta atual é uma continuação?
""")

chain = prompt | model

def tratar_continuacao(state: dict) -> dict:
    pergunta = state["pergunta"].strip()
    ultima = state.get("ultima_pergunta", "").strip()
    topico = state.get("topico_atual", "").strip()

    if not ultima:
        return state 

    resposta = chain.invoke({
        "pergunta_anterior": ultima,
        "pergunta_atual": pergunta
    }).strip().upper()

    if resposta == "SIM":
        state["pergunta"] = (
            f"Continuando sobre {topico}, a pergunta anterior foi: '{ultima}'. "
            f"Agora o usuário quer saber: {pergunta}"
        )

    return state
