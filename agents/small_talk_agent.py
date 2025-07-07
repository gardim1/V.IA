from langchain import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
Você é a **LIA** — Logistics Intelligence Assistant da Sislogica.

• Responda SEM consultar documentos.  
• Mantenha tom profissional, amigável, em português br.  
• Use no máx. 2 emojis.  
• Se a mensagem fugir de small-talk (ex.: pergunta técnica), retorne:
  > Por favor, refaça sua pergunta sobre o TMS para que eu possa ajudar.

Usuário: {pergunta}
LIA:
""")

model = OllamaLLM(model="mistral:7b")

def small_talk_agent(state: dict) -> dict:
    resposta = (prompt | model).invoke({"pergunta":state["pergunta"]})

    return{
        "pergunta": state["pergunta"],
        "resposta": resposta,
        "next": ""
    }
