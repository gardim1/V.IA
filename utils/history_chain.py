from langchain_core.runnables.history import RunnableWithMessageHistory
from utils.history import get_history
from utils.summary import ensure_resumo

def wrap_with_history(pipeline, user_id: str | None):
    resumo = ensure_resumo(user_id)

    return (
        RunnableWithMessageHistory(
            runnable=pipeline.partial(resumo_usuario=resumo),
            get_session_history=get_history,
            input_messages_key="pergunta",
            history_messages_key="chat_history",
        )
        .bind(configurable={"session_id": user_id or 'anon'})
    )
