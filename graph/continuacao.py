#from langchain_ollama import OllamaLLM, OllamaEmbeddings
from llm_provider import get_continuation_llm, get_embed_model
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
import re

#model = OllamaLLM(model="mistral:7b")
#embed_model = OllamaEmbeddings(model="nomic-embed-text")

model = get_continuation_llm()
embed_model = get_embed_model()

prompt = ChatPromptTemplate.from_template("""
Você é um especialista em identificar continuidade em diálogos.

Sua tarefa é detectar se a pergunta atual é uma continuação direta da anterior.

Considere continuação quando:
1. Há elipse:
   - "E na faculdade?"
   - "E os projetos?"
   - "E com Python?"
2. Há pronomes ou termos dependentes de contexto:
   - "isso", "isso aí", "esse projeto", "essa parte", "e nisso?"
3. Mantém a mesma intenção, mudando apenas o foco:
   - "Como foi sua experiência na Sislogica?" → "E na FIAP?"
4. É aprofundamento do mesmo assunto:
   - "Quais seus objetivos?" → "E no curto prazo?"
5. É uma comparação ou extensão natural:
   - "Você trabalha com C#?" → "E com Python?"

Analise APENAS o par de perguntas:

Pergunta anterior: {pergunta_anterior}
Pergunta atual: {pergunta_atual}

Responda APENAS com:
- "SIM" se for continuação clara
- "NÃO" se for pergunta nova
- "INCERTO" se depender de contexto ou estiver ambígua

Exemplos válidos de continuação:
1. Anterior: "Qual sua experiência com IA?" → Atual: "E com RAG?" → SIM
2. Anterior: "Você trabalha na Sislogica?" → Atual: "Fazendo o quê lá?" → SIM
3. Anterior: "Quais são seus projetos?" → Atual: "E o Collaborate?" → SIM
4. Anterior: "Como é sua rotina?" → Atual: "E na faculdade?" → SIM

Exemplos de nova pergunta:
1. Anterior: "Qual sua stack?" → Atual: "Você gosta de viajar?" → NÃO
2. Anterior: "Fala da sua carreira" → Atual: "Qual seu jogo favorito?" → NÃO
""")

chain = prompt | model


def calcular_similaridade(texto1, texto2):
    emb1 = embed_model.embed_query(texto1)
    emb2 = embed_model.embed_query(texto2)
    return cosine_similarity([emb1], [emb2])[0][0]


def extrair_topico_principal(pergunta):
    """
    Extrai o tópico principal da pergunta, usando categorias e variações semânticas.
    Mantém a lógica robusta do projeto original.
    """
    palavras_chave = [
        "IDENTIDADE",
        "VIDA_PESSOAL",
        "RELACIONAMENTOS",
        "FORMACAO",
        "CARREIRA",
        "PROJETOS",
        "HABILIDADES",
        "OBJETIVOS",
        "PREFERENCIAS",
        "SMALL_TALK"
    ]

    pergunta_upper = pergunta.upper()

    for palavra in palavras_chave:
        if palavra in pergunta_upper:
            return palavra

    key_variations = {
        "IDENTIDADE": [
            "QUEM É", "SEU NOME", "QUEM VOCÊ É", "IDADE", "SE APRESENTE",
            "APRESENTAÇÃO", "SOBRE VOCÊ"
        ],
        "VIDA_PESSOAL": [
            "ROTINA", "DIA A DIA", "HÁBITO", "VIDA PESSOAL", "FAMÍLIA",
            "GOSTA", "CURTE", "TEMPO LIVRE", "FINAL DE SEMANA"
        ],
        "RELACIONAMENTOS": [
            "NAMORADA", "NAMORO", "RELACIONAMENTO", "CAROL", "PARCEIRA",
            "VIDA AMOROSA"
        ],
        "FORMACAO": [
            "FACULDADE", "FIAP", "ENGENHARIA DE SOFTWARE", "CURSO",
            "FORMAÇÃO", "ESTUDOS", "SEMESTRE", "MATÉRIA"
        ],
        "CARREIRA": [
            "CARREIRA", "TRABALHO", "EMPRESA", "SISLOGICA", "EXPERIÊNCIA",
            "CURRÍCULO", "ESTÁGIO", "JÚNIOR", "DEV", "EMPREGO", "ATUAÇÃO"
        ],
        "PROJETOS": [
            "PROJETO", "COLLABORATE", "CHATBOT", "RAG", "LIA", "PORTFÓLIO",
            "AUTOMAÇÃO", "API", "FINE-TUNING", "CHROMADB", "N8N", "YOLO"
        ],
        "HABILIDADES": [
            "HABILIDADE", "STACK", "TECNOLOGIA", "PYTHON", "JAVA", "C#",
            "SQL", "REACT", "FASTAPI", "DOCKER", "LANGCHAIN", "BLAZOR"
        ],
        "OBJETIVOS": [
            "OBJETIVO", "META", "PLANOS", "FUTURO", "SONHO", "AMBICÃO",
            "QUER", "PRETENDE", "ROADMAP", "FAANG", "CTO", "CEO"
        ],
        "PREFERENCIAS": [
            "PREFERE", "PREFERÊNCIA", "ESTILO", "GOSTO", "JEITO",
            "COMO GOSTA", "FORMA DE RESPONDER"
        ],
        "SMALL_TALK": [
            "OI", "OLÁ", "TUDO BEM", "VALEU", "OBRIGADO", "BOM DIA"
        ]
    }

    for key, variations in key_variations.items():
        for variation in variations:
            if variation in pergunta_upper:
                return key

    palavras = re.findall(r'\b[A-Z]{3,}\b', pergunta_upper) or re.findall(r'\b\w{5,}\b', pergunta_upper)
    if palavras:
        return palavras[0]

    return "IDENTIDADE"


def reconstruir_pergunta_eliptica(pergunta_atual, ultima_pergunta, topico_atual):
    """
    Reconstrói perguntas curtas dependentes de contexto.
    Mantém a lógica forte, mas adaptada ao domínio pessoal.
    """
    atual = pergunta_atual.strip()
    atual_lower = atual.lower()

    if atual_lower.startswith(("e ", "e a ", "e o ", "e as ", "e os ")):
        base = ultima_pergunta.rstrip(" ?")
        complemento = re.sub(r"^e\s+", "", atual, flags=re.I).strip().rstrip("?")
        return f"{base} {complemento}?"

    if atual_lower in {"e?", "e isso?", "e nessa parte?", "e nisso?", "e quanto a isso?"}:
        return f"{topico_atual}: {atual}"

    if len(atual.split()) <= 4:
        return f"{topico_atual}: {atual}"

    return f"{topico_atual}: {atual}"


def tratar_continuacao(state: dict) -> dict:
    pergunta_atual = state["pergunta"].strip()
    ultima_pergunta = state.get("ultima_pergunta", "").strip()
    topico_atual = state.get("topico_atual", "IDENTIDADE").strip()

    if not ultima_pergunta:
        state["topico_atual"] = extrair_topico_principal(pergunta_atual)
        return state

    resposta = chain.invoke({
        "pergunta_anterior": ultima_pergunta,
        "pergunta_atual": pergunta_atual
    }).strip().upper()

    state["continuidade_count"] = state.get("continuidade_count", 0) + (1 if resposta == "SIM" else 0)

    if resposta == "SIM":
        state["pergunta"] = reconstruir_pergunta_eliptica(
            pergunta_atual=pergunta_atual,
            ultima_pergunta=ultima_pergunta,
            topico_atual=topico_atual
        )
        state["topico_atual"] = extrair_topico_principal(state["pergunta"])

    elif resposta == "INCERTO":
        similaridade = calcular_similaridade(pergunta_atual, ultima_pergunta)

        if similaridade > 0.65:
            state["pergunta"] = reconstruir_pergunta_eliptica(
                pergunta_atual=pergunta_atual,
                ultima_pergunta=ultima_pergunta,
                topico_atual=topico_atual
            )
            state["continuidade_count"] = state.get("continuidade_count", 0) + 1
            state["topico_atual"] = extrair_topico_principal(state["pergunta"])
        else:
            state["topico_atual"] = extrair_topico_principal(pergunta_atual)

    else:
        state["topico_atual"] = extrair_topico_principal(pergunta_atual)

    if state.get("continuidade_count", 0) > 3:
        print(f"[ALERTA] Cadeia longa de continuidade ({state['continuidade_count']}) - Verificar contexto")
        if ":" in state["pergunta"]:
            state["pergunta"] = state["pergunta"].split(":", 1)[1].strip()

    return state