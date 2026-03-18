from agents.base_rag_agent import run_rag_agent

def objetivos_agent(state: dict) -> dict:
    return run_rag_agent(state, "OBJETIVOS", "OBJETIVOS")