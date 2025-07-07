from langchain_core.runnables.history import RunnableWithMessageHistory
from utils import get_history

def wrap_with_history(pipeline, user_id: str):

    return RunnableWithMessageHistory(
        runnable=pipeline,
        get_session_history=get_history,
        input_messages_key="pergunta",
        history_messages_key="chat_history",
    ).bind(configurable={"session_id": user_id})