from itertools import count
from typing import Literal

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class Message(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str


app = FastAPI(title="AITH Demo Backend", version="0.1.0")

# Allow the Vite dev server to talk to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory store; resets each time the server restarts.
_ids = count(1)
_messages = [
    Message(
        id=next(_ids),
        role="assistant",
        content="Hello! Ask me anything and I'll echo it back.",
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
    Stores the user message and returns a mocked assistant reply.
    """
    user_message = Message(id=next(_ids), role="user", content=message_text)
    _messages.append(user_message)

    assistant_reply = Message(
        id=next(_ids), role="assistant", content=f"I heard you say: {message_text}"
    )
    _messages.append(assistant_reply)

    return assistant_reply
