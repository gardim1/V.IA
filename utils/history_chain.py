from langchain_core.runnables.history import RunnableWithMessageHistory
from utils import get_history
from utils.summary import resumo_ja_gerado, gerar_resumo_via_llm, carregar_resumo

def wrap_with_history(pipeline, user_id: str):
    user_id = user_id or "anon"

    if not resumo_ja_gerado(user_id):
        gerar_resumo_via_llm(user_id)

    resumo = carregar_resumo(user_id)

    return RunnableWithMessageHistory(
        runnable=pipeline.partial(resumo_usuario=resumo),
        get_session_history=get_history,
        input_messages_key="pergunta",
        history_messages_key="chat_history",
    ).bind(configurable={"session_id": user_id})