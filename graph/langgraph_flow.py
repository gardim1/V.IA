from typing import TypedDict
from langgraph.graph import StateGraph, END

from graph.roteador import roteador_tool
from agents.cte_mdfe_agent      import cte_mdfe_agent
from agents.roteirizacao_agent  import roteirizacao_agent
from agents.geral_agent         import geral_agent
from agents.small_talk_agent import small_talk_agent

class GraphState(TypedDict):
    pergunta: str
    resposta: str
    next: str

builder = StateGraph(GraphState)

# nós
builder.add_node("roteador",     roteador_tool)
builder.add_node("cte_mdfe",     cte_mdfe_agent)
builder.add_node("roteirizacao", roteirizacao_agent)
builder.add_node("geral",        geral_agent)
builder.add_node("small_talk",   small_talk_agent)

builder.set_entry_point("roteador")

# roteamento condicional
builder.add_conditional_edges(
    "roteador",
    lambda s: s["next"],
    {
        "cte_mdfe":     "cte_mdfe",
        "roteirizacao": "roteirizacao",
        "geral":        "geral",
        "small_talk":   "small_talk",
    },
)

# nós finais
builder.add_edge("cte_mdfe",     END)
builder.add_edge("roteirizacao", END)
builder.add_edge("geral",        END)
builder.add_edge("small_talk",   END)

langgraph_flow = builder.compile()
