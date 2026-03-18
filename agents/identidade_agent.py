from agents.base_rag_agent import run_rag_agent

def identidade_agent(state: dict) -> dict:
    return run_rag_agent(state, "IDENTIDADE", "IDENTIDADE")