import json
from utils.db_loader import Neo4jLoader
from utils.llm import LLMWorker
from utils.config_loader import config
from utils.rag import RAG
import asyncio


async def main():
    loader = Neo4jLoader()
    loader.load2db()
    rag = RAG()
    s = await rag.run('Кто отец валентины?')
    print(s)
asyncio.run(main())