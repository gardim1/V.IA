from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda          # ⬅️ novo
from utils.history import get_history
from utils.summary import ensure_resumo

def wrap_with_history(pipeline, user_id: str | None):
    """
    Recebe `pipeline = prompt | model` de qualquer agente,
    injeta `resumo_usuario` e devolve o RunnableWithMessageHistory.
    NÃO exige que o pipeline tenha .partial().
    """
    if user_id is None:
        raise ValueError("user_id ausente - obrigatório em produção")

    resumo = ensure_resumo(user_id)

    def _run(vars):
        vars = dict(vars)
        vars["resumo_usuario"] = resumo
        return pipeline.invoke(vars)     

    pipeline_wrapped = RunnableLambda(_run)

    return (
        RunnableWithMessageHistory(
            runnable=pipeline_wrapped,
            get_session_history=get_history,
            input_messages_key="pergunta",
            history_messages_key="chat_history",
        )
        .bind(configurable={"session_id": user_id})
    )
