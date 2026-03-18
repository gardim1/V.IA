from agents.base_rag_agent import run_rag_agent

def projetos_agent(state: dict) -> dict:
    return run_rag_agent(state, "PROJETOS", "PROJETOS")