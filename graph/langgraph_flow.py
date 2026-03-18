from typing import TypedDict
from langgraph.graph import StateGraph, END

from graph.roteador import roteador_tool
from graph.continuacao import tratar_continuacao

from agents.identidade_agent import identidade_agent
from agents.vida_pessoal_agent import vida_pessoal_agent
from agents.relacionamentos_agent import relacionamentos_agent
from agents.formacao_agent import formacao_agent
from agents.carreira_agent import carreira_agent
from agents.projetos_agent import projetos_agent
from agents.habilidades_agent import habilidades_agent
from agents.objetivos_agent import objetivos_agent
from agents.preferencias_agent import preferencias_agent
from agents.small_talk_agent import small_talk_agent

class GraphState(TypedDict):
    pergunta: str
    resposta: str
    next: str
    user_id: str
    ultima_pergunta: str
    topico_atual: str
    continuidade_count: int

builder = StateGraph(GraphState)

builder.add_node("roteador", roteador_tool)
builder.add_node("tratar_continuacao", tratar_continuacao)

builder.add_node("small_talk", small_talk_agent)
builder.add_node("identidade", identidade_agent)
builder.add_node("vida_pessoal", vida_pessoal_agent)
builder.add_node("relacionamentos", relacionamentos_agent)
builder.add_node("formacao", formacao_agent)
builder.add_node("carreira", carreira_agent)
builder.add_node("projetos", projetos_agent)
builder.add_node("habilidades", habilidades_agent)
builder.add_node("objetivos", objetivos_agent)
builder.add_node("preferencias", preferencias_agent)

builder.set_entry_point("roteador")
builder.add_edge("roteador", "tratar_continuacao")

builder.add_conditional_edges(
    "tratar_continuacao",
    lambda s: s["next"],
    {
        "small_talk": "small_talk",
        "identidade": "identidade",
        "vida_pessoal": "vida_pessoal",
        "relacionamentos": "relacionamentos",
        "formacao": "formacao",
        "carreira": "carreira",
        "projetos": "projetos",
        "habilidades": "habilidades",
        "objetivos": "objetivos",
        "preferencias": "preferencias",
    },
)

builder.add_edge("small_talk", END)
builder.add_edge("identidade", END)
builder.add_edge("vida_pessoal", END)
builder.add_edge("relacionamentos", END)
builder.add_edge("formacao", END)
builder.add_edge("carreira", END)
builder.add_edge("projetos", END)
builder.add_edge("habilidades", END)
builder.add_edge("objetivos", END)
builder.add_edge("preferencias", END)

langgraph_flow = builder.compile()