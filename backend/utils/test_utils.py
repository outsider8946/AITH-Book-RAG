import json
import os
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    answer_correctness,
    context_precision,
    context_recall,
)
from ragas import evaluate
from backend.utils.config_loader import config
from backend.utils.llm import EmbeddingMistral, LLMMistral
from datasets import Dataset
from tqdm.asyncio import tqdm_asyncio
from backend.utils.rag import RAG
from dotenv import load_dotenv

load_dotenv()


class TestRAG:
    def __init__(self):
        self.test_dataset = json.load(open("./backend/data/test/questions.json"))
        self.llm = LLMMistral(config)
        self.embeddings = EmbeddingMistral(config)
        self.rag = RAG()
        os.environ["RAGAS_DISABLE_ASYNC"] = "1"
        
        
    async def get_rag_answers(self):
        tasks = [self.rag.run(query=item) for item in self.test_dataset["question"]]

        if len(tasks) > 0:
            results = await tqdm_asyncio.gather(*tasks, desc="RAG answer processing")
            for i, r in enumerate(results):
                print("ANSWER:", r["answer"])
                self.test_dataset["contexts"][i] = r["context_used"]
                self.test_dataset["answer"][i] = r["answer"]

        with open("./backend/data/test/questions.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.test_dataset, indent=4, ensure_ascii=False))

    def compute_metrics(self):
        test_dataset = Dataset.from_dict(
            json.load(open("./backend/data/test/questions.json"))
        )
        metrics = [faithfulness, answer_relevancy, answer_correctness, context_precision, context_recall]

        result = evaluate(
            dataset=test_dataset,
            metrics=metrics,
            llm=self.llm,
            embeddings=self.embeddings,
            raise_exceptions=False
        )

        print("\n📊 Результаты RAGAS:")
        print(result)
