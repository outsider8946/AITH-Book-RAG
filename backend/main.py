import logging
import sys
from itertools import count
from typing import Literal
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from .utils.rag import RAG
from .utils.downloader import Downloader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Message(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str


app = FastAPI(title="AITH Demo Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "bolt://neo4j-db:7687",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    downloader = Downloader()
    await downloader.download()


rag = RAG()
logger.info("RAG система инициализирована")

_ids = count(1)
_messages = [
    Message(
        id=next(_ids),
        role="assistant",
        content="Привет! Я помощник по роману 'Граф Монте-Кристо'. Задайте мне вопрос о романе!",
    )
]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/messages", response_model=list[Message])
async def get_messages() -> list[Message]:
    return _messages


@app.post("/api/messages", response_model=Message)
async def post_message(message_text: str = Body(..., embed=False)) -> Message:
    """
    Accepts a plain string body (e.g. axios.post('/api/messages', 'hi')).
    Stores the user message and uses RAG to generate an assistant reply.
    """
    user_message = Message(id=next(_ids), role="user", content=message_text)
    _messages.append(user_message)

    try:
        chat_history = []
        for msg in _messages[-10:]:
            chat_history.append({"role": msg.role, "content": msg.content})

        logger.info(f"Обработка запроса: {message_text[:50]}...")
        rag_result = await rag.run(query=message_text, chat_history=chat_history)

        answer_content = rag_result.get(
            "answer", "Извините, не удалось сгенерировать ответ."
        )

        assistant_reply = Message(
            id=next(_ids), role="assistant", content=answer_content
        )
        _messages.append(assistant_reply)

        logger.info(f"Ответ сгенерирован. Длина: {len(answer_content)} символов")
        if rag_result.get("graph_metadata"):
            logger.info(
                f"Использованы данные из графа. Найдено связей: {len(rag_result['graph_metadata'])}"
            )

        return assistant_reply

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
        error_message = Message(
            id=next(_ids),
            role="assistant",
            content="Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.",
        )
        _messages.append(error_message)
        return error_message
