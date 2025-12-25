from utils.rag import RAG
import asyncio


async def main():
    rag = RAG()
    s = await rag.run("Кто отец валентины?")
    print(s)


asyncio.run(main())
