import os 
import redis
from dotenv import load_dotenv
from langchain_community.chat_message_histories import RedisChatMessageHistory

load_dotenv()

CHAT_TTL_SECONDS = int(os.getenv("CHAT_TTL_SECONDS", "2592000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)

def get_history(session_id: str):
    key = f"message_store:{session_id}"
    redis_client.expire(key, CHAT_TTL_SECONDS)
    return RedisChatMessageHistory(
        session_id=session_id,
        url=REDIS_URL,
        #ttl=CHAT_TTL_SECONDS
    )