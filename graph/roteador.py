#from langchain_ollama import OllamaLLM
from llm_provider import get_router_llm
from langchain_core.prompts import PromptTemplate
import re

prompt = PromptTemplate.from_template("""
Classifique a pergunta abaixo em UMA das categorias:

IDENTIDADE, VIDA_PESSOAL, RELACIONAMENTOS, FORMACAO, CARREIRA,
PROJETOS, HABILIDADES, OBJETIVOS, PREFERENCIAS.

Se a pergunta for trivial, saudação ou cortesia, classifique como SMALL_TALK.

IDENTIDADE:
    - Quem é você?
    - Qual seu nome?
    - Quantos anos você tem?
    - Me fala sobre você
    - Se apresenta

VIDA_PESSOAL:
    - Como é sua rotina?
    - O que você gosta de fazer?
    - Como é seu dia a dia?
    - O que faz no tempo livre?
    - Como é sua vida fora do trabalho?

RELACIONAMENTOS:
    - Você namora?
    - Quem é sua namorada?
    - Como é seu relacionamento?
    - Fala da Carol
    - Como vocês se conheceram?

FORMACAO:
    - Você faz faculdade?
    - O que você estuda?
    - Fala da FIAP
    - Em que semestre você está?
    - Como é sua formação?

CARREIRA:
    - Onde você trabalha?
    - Qual sua experiência profissional?
    - Fala da sua carreira
    - Qual seu currículo?
    - O que você faz na Sislogica?

PROJETOS:
    - Quais projetos você está fazendo?
    - Fala do Collaborate
    - Como funciona sua IA com RAG?
    - Quais APIs você já criou?
    - Quais projetos você quer lançar?

HABILIDADES:
    - Quais tecnologias você domina?
    - Você sabe Python?
    - Você trabalha com Java?
    - Qual sua stack?
    - O que você sabe de IA?

OBJETIVOS:
    - Quais seus objetivos?
    - Onde você quer chegar?
    - Quais suas metas?
    - Você quer ser CTO?
    - Quais seus planos para o futuro?

PREFERENCIAS:
    - Como você prefere aprender?
    - Como gosta de responder?
    - Quais suas preferências?
    - O que você valoriza?
    - Qual seu estilo?

Responda APENAS com o nome exato da categoria, sem explicações.

Pergunta: {pergunta}
Categoria:
""")

model = get_router_llm()
chain = prompt | model

SMALL_TALK_PATTERNS = re.compile(
    r"^(oi|olá|ola|bom dia|boa tarde|boa noite|tudo bem\??|e ai|e aí|valeu|obrigado|obrigada)\s*$",
    re.I
)


def roteador_tool(state: dict) -> dict:
    pergunta = state["pergunta"].strip()
    user_id = state.get("user_id")

    if SMALL_TALK_PATTERNS.match(pergunta):
        categoria = "SMALL_TALK"
    else:
        categoria = chain.invoke({"pergunta": pergunta}).strip().upper()

    validas = {
        "SMALL_TALK",
        "IDENTIDADE",
        "VIDA_PESSOAL",
        "RELACIONAMENTOS",
        "FORMACAO",
        "CARREIRA",
        "PROJETOS",
        "HABILIDADES",
        "OBJETIVOS",
        "PREFERENCIAS"
    }

    if categoria not in validas:
        categoria = "IDENTIDADE"

    return {
        "pergunta": pergunta,
        "resposta": "",
        "next": categoria.lower(),
        "user_id": user_id,
        "ultima_pergunta": state.get("ultima_pergunta", ""),
        "topico_atual": categoria,
        "continuidade_count": state.get("continuidade_count", 0)
    }