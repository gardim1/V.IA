from agents.base_rag_agent import run_rag_agent

def preferencias_agent(state: dict) -> dict:
    return run_rag_agent(state, "PREFERENCIAS", "PREFERENCIAS")