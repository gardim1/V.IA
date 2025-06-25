from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from graph.roteador import roteador_tool

from agents.cte_mdfe_agent import cte_mdfe_agent
from agents.roteirizacao_agent import roteirizacao_agent
from agents.geral_agent import geral_agent  
from typing import TypedDict

class GraphState(TypedDict):
    pergunta: str
    resposta: str
    next: str

builder = StateGraph(GraphState)


builder.add_node("roteador", ToolNode(roteador_tool))
builder.add_node("cte_mdfe",      cte_mdfe_agent)
builder.add_node("roteirizacao",  roteirizacao_agent)
builder.add_node("geral",         geral_agent)

builder.set_entry_point("roteador")

builder.add_edge("roteador", lambda s: s["next"])

builder.add_edge("cte_mdfe",     END)
builder.add_edge("roteirizacao", END)
builder.add_edge("geral",        END)

langgraph_flow = builder.compile()
