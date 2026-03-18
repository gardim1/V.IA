from agents.base_rag_agent import run_rag_agent

def formacao_agent(state: dict) -> dict:
    return run_rag_agent(state, "FORMACAO", "FORMACAO")