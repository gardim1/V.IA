from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

model = OllamaLLM(model="mistral:7b")
embed_model = OllamaEmbeddings(model="nomic-embed-text")

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
2. Anterior: "Preciso emitir um CT-e" → Atual: "Como fazer para MDFE?" → SIM
3. Anterior: "O sistema está lento" → Atual: "E na roteirização?" → SIM
""")

chain = prompt | model

def calcular_similaridade(texto1, texto2):
    """Calcula similaridade entre embeddings dos textos"""
    emb1 = embed_model.embed_query(texto1)
    emb2 = embed_model.embed_query(texto2)
    return cosine_similarity([emb1], [emb2])[0][0]

def extrair_topico_principal(pergunta):
    """Extrai o tópico principal baseado nas palavras-chave do TMS"""
    palavras_chave = ["CTE_MDFE", "ROTEIRIZACAO", "RELATORIOS", "DEVOLUCAO",
                      "CHAMADOS", "TRANSPORTADORA", "FROTA", "INDENIZACAO", "GERAL"]
    
    pergunta_upper = pergunta.upper()
    for palavra in palavras_chave:
        if palavra in pergunta_upper:
            return palavra
    
    key_variations = {
        "CTE_MDFE": ["CTE", "MDFE", "CONHECIMENTO", "DOCUMENTO FISCAL"],
        "ROTEIRIZACAO": ["ROTEIRIZAÇÃO", "ROTA", "ENTREGAS", "OTIMIZAR ROTA"],
        "RELATORIOS": ["RELATÓRIO", "REPORT", "DASHBOARD"],
        "DEVOLUCAO": ["DEVOLUÇÃO", "RETORNO", "MERCADORIA DEVOLVIDA"],
        "CHAMADOS": ["CHAMADO", "SUPORTE", "TICKET", "INCIDENTE"],
        "TRANSPORTADORA": ["TRANSPORTADOR", "OPERADOR LOGÍSTICO", "OL"],
        "FROTA": ["VEÍCULO", "CAMINHÃO", "CARRO", "MOTORISTA"],
        "INDENIZACAO": ["INDENIZAÇÃO", "SEGURO", "REEMBOLSO", "COMPENSAÇÃO"],
        "GERAL": ["CONFIGURAÇÃO", "AJUDA", "DÚVIDA", "SISTEMA"]
    }
    
    for key, variations in key_variations.items():
        for variation in variations:
            if variation in pergunta_upper:
                return key
    
    palavras = re.findall(r'\b[A-Z]{3,}\b', pergunta_upper) or re.findall(r'\b\w{5,}\b', pergunta_upper)
    if palavras:
        return palavras[0]
    
    return "GERAL"  

def tratar_continuacao(state: dict) -> dict:
    pergunta_atual = state["pergunta"].strip()
    ultima_pergunta = state.get("ultima_pergunta", "").strip()
    topico_atual = state.get("topico_atual", "GERAL").strip()  

    if not ultima_pergunta:
        return state

    resposta = chain.invoke({
        "pergunta_anterior": ultima_pergunta,
        "pergunta_atual": pergunta_atual
    }).strip().upper()

    state["continuidade_count"] = state.get("continuidade_count", 0) + (1 if resposta=="SIM" else 0)

    if resposta == "SIM":
        if pergunta_atual.lower().startswith(("e ", "e?", "e\n", "e a")):
            acao = ultima_pergunta.split('?')[0].strip()
            novo_objeto = pergunta_atual[1:].strip().rstrip('?')
            state["pergunta"] = f"{acao} {novo_objeto}?"
        else:
            state["pergunta"] = f"{topico_atual}: {pergunta_atual}"
        
        state["topico_atual"] = extrair_topico_principal(state["pergunta"])
    
    elif resposta == "INCERTO":
        similaridade = calcular_similaridade(pergunta_atual, ultima_pergunta)
        if similaridade > 0.65:
            state["pergunta"] = f"{topico_atual}: {pergunta_atual}"
            state["continuidade_count"] = state.get("continuidade_count", 0) + 1
            state["topico_atual"] = extrair_topico_principal(state["pergunta"])
    
    if state.get("continuidade_count", 0) > 3:
        print(f"[ALERTA] Cadeia longa de continuidade ({state['continuidade_count']}) - Verificar contexto")
        if ":" in state["pergunta"]:
            state["pergunta"] = state["pergunta"].split(":", 1)[1].strip()
    
    return state

if __name__ == "__main__":
    state = {
        "pergunta": "E MDFE?",
        "ultima_pergunta": "Como emitir CTE?",
        "topico_atual": "CTE_MDFE"
    }
    
    print("Antes:", state)
    state = tratar_continuacao(state)
    print("\nDepois:", state)
    print("Pergunta reconstruída:", state["pergunta"])
    print("Tópico atual:", state["topico_atual"])