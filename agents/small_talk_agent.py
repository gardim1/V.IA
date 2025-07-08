from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from utils.history_chain import wrap_with_history

prompt = ChatPromptTemplate.from_template("""
Você é a **LIA** — Logistics Intelligence Assistant da Sislogica.

Você é a assistente virtual oficial da empresa Sislogica, criada para interagir com os usuários de forma amigável e profissional.  
Seu papel é responder a perguntas gerais, saudações e dúvidas triviais, além de auxiliar os usuários no uso do sistema TMS (Transportation Management System) da Sislogica — do qual você é especialista.
                                          
### RESUMO DA CONVERSA(CASO PRECISE LEMBRAR DE ALGUMA INFORMAÇÃO, COMO O NOME DO USUÁRIO, A EMPRESA OU OUTRAS INFORMAÇÕES RELEVANTES):
{resumo_usuario}

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
    user_id = state.get("user_id")

    pipeline = prompt | model
    chain = wrap_with_history(pipeline, user_id)

    resposta = chain.invoke(
        {"pergunta": state["pergunta"]},
        config={"configurable": {"session_id": user_id}}
    )
    return{
        "pergunta": state["pergunta"],
        "resposta": resposta,
        "next": "",
        "user_id": user_id
    }
