from utils.db_loader import Neo4jLoader
from utils.rag import RAG
import asyncio


async def main():
    loader = Neo4jLoader()
    loader.load2db()
    rag = RAG()
    await rag.run("Кто арестовал Эдмона Дантеса?")


asyncio.run(main())
