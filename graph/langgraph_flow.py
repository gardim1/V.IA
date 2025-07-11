from typing import TypedDict
from langgraph.graph import StateGraph, END

from graph.roteador import roteador_tool
from agents.cte_mdfe_agent      import cte_mdfe_agent
from agents.roteirizacao_agent  import roteirizacao_agent
from agents.geral_agent         import geral_agent
from agents.small_talk_agent import small_talk_agent
from agents.relatorios_agent     import relatorios_agent
from agents.devolucao_agent      import devolucao_agent
from agents.transportadora_agent import transportadora_agent
from agents.frota_agent          import frota_agent
from agents.indenizacao_agent    import indenizacao_agent
from agents.chamados_agent       import chamados_agent
from graph.continuacao import tratar_continuacao

class GraphState(TypedDict):
    pergunta: str
    resposta: str
    next: str
    user_id: str 

builder = StateGraph(GraphState)

# nós
builder.add_node("roteador",     roteador_tool)
builder.add_node("cte_mdfe",     cte_mdfe_agent)
builder.add_node("roteirizacao", roteirizacao_agent)
builder.add_node("geral",        geral_agent)
builder.add_node("small_talk",   small_talk_agent)
builder.add_node("relatorios",     relatorios_agent)
builder.add_node("devolucao",      devolucao_agent)
builder.add_node("transportadora", transportadora_agent)
builder.add_node("frota",          frota_agent)
builder.add_node("indenizacao",    indenizacao_agent)
builder.add_node("chamados",       chamados_agent)
builder.add_node("tratar_continuacao", tratar_continuacao)

builder.set_entry_point("roteador")

#verificação de continuidade
builder.add_edge("roteador", "tratar_continuacao")

# roteamento condicional
builder.add_conditional_edges(
    "tratar_continuacao",
    lambda s: s["next"],
    {
        "cte_mdfe":     "cte_mdfe",
        "roteirizacao": "roteirizacao",
        "geral":        "geral",
        "small_talk":   "small_talk",
        "relatorios":     "relatorios",
        "devolucao":      "devolucao",
        "transportadora": "transportadora",
        "frota":          "frota",
        "indenizacao":    "indenizacao",
        "chamados":       "chamados",
    },
)

# nós finais
builder.add_edge("cte_mdfe",       END)
builder.add_edge("roteirizacao",   END)
builder.add_edge("geral",          END)
builder.add_edge("small_talk",     END)
builder.add_edge("relatorios",     END)
builder.add_edge("devolucao",      END)
builder.add_edge("transportadora", END)
builder.add_edge("frota",          END)
builder.add_edge("indenizacao",    END)
builder.add_edge("chamados",       END)

langgraph_flow = builder.compile()
