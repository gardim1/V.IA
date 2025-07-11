from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="mistral:7b")

prompt = ChatPromptTemplate.from_template("""
Você é um especialista em identificar continuidade em diálogos. Sua tarefa é detectar se a pergunta atual é uma continuação direta da anterior, usando estes critérios:
1. É uma elipse (ex: "E veículos?" que continua o assunto anterior)
2. Usa pronomes ou artigos que remetem ao contexto anterior ("isso", "os documentos")
3. Mantém a mesma ação/intenção mas muda o objeto
4. É uma sub-pergunta do mesmo tópico

Analise APENAS o par de perguntas:

Pergunta anterior: {pergunta_anterior}
Pergunta atual: {pergunta_atual}

Responda APENAS com:
- "SIM" se for continuação clara
- "NÃO" se for pergunta nova
- "INCERTO" se precisar de mais contexto

Exemplos válidos de continuação:
1. Anterior: "Como cadastrar motoristas?" → Atual: "E veículos?" → SIM
2. Anterior: "Preciso emitir um CT-e" → Atual: "Como fazer para nfe?" → SIM
3. Anterior: "O sistema está lento" → Atual: "E no módulo de fretes?" → SIM
""")

chain = prompt | model

def tratar_continuacao(state: dict) -> dict:
    pergunta_atual = state["pergunta"].strip()
    ultima_pergunta = state.get("ultima_pergunta", "").strip()
    topico_atual = state.get("topico_atual", "").strip()

    if not ultima_pergunta or not topico_atual:
        return state

    resposta = chain.invoke({
        "pergunta_anterior": ultima_pergunta,
        "pergunta_atual": pergunta_atual
    }).strip().upper()

    if resposta == "SIM":
        if pergunta_atual.lower().startswith(("e ", "e?", "e\n")):
            acao = ultima_pergunta.split('?')[0].strip()
            novo_objeto = pergunta_atual[1:].strip().rstrip('?')
            state["pergunta"] = f"{acao} {novo_objeto}?"
        else:
            state["pergunta"] = f"{topico_atual}: {pergunta_atual}"

    return state