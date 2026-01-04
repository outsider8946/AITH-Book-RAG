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
from openai import OpenAI
from ..utils.config_loader import config
from ragas.llms import llm_factory
from datasets import Dataset
from tqdm.asyncio import tqdm_asyncio
from ..utils.rag import RAG
from dotenv import load_dotenv

load_dotenv()


class TestRAG:
    def __init__(self):
        self.questions = json.load(open("./data/test/dummy_questions.json"))
        self.rag = RAG()
        os.environ["RAGAS_DISABLE_ASYNC"] = "1"
        self.llm = self._get_test_llm()

    def _get_test_llm(self):
        if config.llm.type == "depseek":
            model_name = (config.llm.deepseek_model_name,)
            api_key = (os.environ.get("DEEPSEEK_API_KEY"),)
            base_url = "https://api.deepseek.com"
        else:
            model_name = config.llm.mistral_model_name
            api_key = os.environ.get("MISTRAL_API_KEY")
            base_url = "https://api.mistral.ai/v1"

        return llm_factory(
            model_name, client=OpenAI(api_key=api_key, base_url=base_url)
        )

    import json

    def _convert_to_ragas_format(self, input_path: str, output_path: str):
        # Загрузка
        with open(input_path, "r", encoding="utf-8") as f:
            rows = json.load(f)

        # Инициализация колонок
        columns = {
            "question": [],
            "answer": [],
            "contexts": [],  # ← обязательно contexts, не context!
            "ground_truth": [],
        }

        for row in rows:
            # Вопрос и ответ — строки
            columns["question"].append(row.get("question", ""))
            columns["answer"].append(row.get("answer", ""))
            columns["ground_truth"].append(row.get("ground_truth", ""))

            # Контекст — нормализуем в List[str]
            ctx = row.get("context", [])
            if isinstance(ctx, str) and ctx.strip():
                # Разбиваем по пустым строкам (как у вас в данных)
                chunks = [c.strip() for c in ctx.split("\n\n") if c.strip()]
                columns["contexts"].append(chunks)
            elif isinstance(ctx, list):
                # Уже список — оставляем, но убеждаемся, что строки
                columns["contexts"].append([str(x) for x in ctx if x])
            else:
                columns["contexts"].append([])  # пустой список

        # Сохранение в правильном формате
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(columns, f, ensure_ascii=False, indent=2)

    async def get_rag_answers(self):
        test_result = []
        tasks = [self.rag.run(query=item["question"]) for item in self.questions]

        if len(tasks) > 0:
            results = await tqdm_asyncio.gather(*tasks, desc="RAG answer processing")
            for result_item, question_item in zip(results, self.questions):
                test_result.append(
                    {
                        "question": question_item["question"],
                        "ground_truth": question_item["ground_truth"],
                        "answer": question_item["answer"],
                        "real_answer": result_item["answer"],
                        "context": result_item["llm_context"],
                    }
                )

        return test_result

    def compute_metrics(self):
        self._convert_to_ragas_format(
            "./data/test/test_result.json", "./data/test/ragas_input.json"
        )
        test_dataset = Dataset.from_dict(
            json.load(open("./data/test/ragas_input.json"))
        )
        metrics = [
            faithfulness,
            answer_relevancy,
            answer_correctness,
            context_precision,
            context_recall,
        ]

        result = evaluate(
            dataset=test_dataset, metrics=metrics, llm=self.llm, raise_exceptions=False
        )

        print("\n📊 Результаты RAGAS:")
        print(result)
        print("\n→ Средние значения:")
        for metric in metrics:
            avg = result[metric.name]
            if isinstance(avg, list):
                avg = sum(avg) / len(avg)
            print(f"  {metric.name}: {avg:.3f}")
