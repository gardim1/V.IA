from agents.base_rag_agent import run_rag_agent

def vida_pessoal_agent(state: dict) -> dict:
    return run_rag_agent(state, "VIDA_PESSOAL", "VIDA_PESSOAL")