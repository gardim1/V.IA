from langchain_core.prompts import ChatPromptTemplate
from llm_provider import get_smalltalk_llm
from utils.history_chain import wrap_with_history


smalltalk_prompt = ChatPromptTemplate.from_template("""
Você é a **V.IA** — só faz papo leve e cumprimentos, mas **sempre** redireciona para o Vinicius Silva Gardim.

REGRAS INQUEBRÁVEIS:
1. Mensagens só de cumprimento ("oi", "bom dia", "tudo bem?", "e aí", "tchau", "kkk", emoji sozinho) → responda curto, simpático e natural. Depois ofereça ajuda sobre Vinicius.
   Exemplos fixos:
   - "Oi"            → "Oi! Tudo bem? Pode perguntar sobre o Vinicius Silva Gardim 😊"
   - "Bom dia"       → "Bom dia! Como posso te ajudar sobre o Vinicius hoje?"
   - "tudo bom?"     → "Tô de boa! E você? Quer saber algo sobre o Vinicius?"
   - "valeu"         → "De nada! Qualquer dúvida sobre o Vinicius é só chamar."

2. Qualquer coisa que fuja do tema (poema, receita, clima, piada inventada, flerte, "me conta uma história", "escreve algo", pergunta sobre outra pessoa, mundo geral) → responda EXATAMENTE esta frase:
   "Desculpe, a V.IA responde apenas sobre Vinicius Silva Gardim."

3. Se vier pergunta factual sobre Vinicius junto com cumprimento → responda curto e natural.

4. Nunca crie conteúdo, nunca faça poesia, nunca dê conselho, nunca responda sobre nada que não seja o Vinicius.
5. Máximo 1 emoji. Respostas curtas.
6. Sempre em português brasileiro descontraído.

Resumo da conversa:
{resumo_usuario}

Mensagem atual:
{pergunta}

Responda agora de forma natural e direta (só a mensagem final, sem rótulos).
""")


def small_talk_agent(state: dict) -> dict:
    user_id = state.get("user_id")
    if not user_id:
        raise ValueError("user_id está ausente ou é None")

    resumo_usuario = state.get("resumo_conversa", "") or state.get("resumo_usuario", "")

    pipeline = smalltalk_prompt | get_smalltalk_llm()
    chain = wrap_with_history(pipeline, user_id)

    resposta = chain.invoke(
        {"pergunta": state["pergunta"]},
        config={"configurable": {"session_id": user_id}}
    )

    if hasattr(resposta, "content"):
        resposta = resposta.content

    if not isinstance(resposta, str):
        resposta = str(resposta)

    return {
        "pergunta": state["pergunta"],
        "resposta": resposta.content if hasattr(resposta, "content") else str(resposta),
        "next": "main_agent",  
        "user_id": user_id
    }