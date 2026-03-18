from agents.base_rag_agent import run_rag_agent

def carreira_agent(state: dict) -> dict:
    return run_rag_agent(state, "CARREIRA", "CARREIRA")