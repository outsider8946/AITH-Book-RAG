from backend.utils.test_utils import TestRAG
import asyncio
import logging


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d → %(message)s",
        datefmt="%H:%M:%S",
        force=True,  # ← критично, если запускаете повторно
    )
    test = TestRAG()
    await test.get_rag_answers_1()
    test.compute_metrics()


asyncio.run(main())
