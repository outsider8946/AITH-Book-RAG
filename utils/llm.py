import os
from pydantic import BaseModel
from typing import Dict, Optional, Type, TypeVar, List
from pydantic import SecretStr
from omegaconf import DictConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_core.embeddings import Embeddings
from utils.templates import (
    FEATURE_EXTRACT_TEMPLATE,
    CANONICAL_NAMES_TEMPLATE,
    ANSWER_TEMPLATE,
    QUERY2GRAPH_TEMPLATE,
    CHAPTER_SUMMARY_TEMPLATE,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from models import EntitiesRelationships, CanonicalName, Query

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMDeepSeek(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ.get("DEEPSEEK_API_KEY") or ""),
            model=config.llm.deepseek_model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
            max_retries=3,
            timeout=60,
        )


class LLMMistral(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://api.mistral.ai/v1",
            api_key=SecretStr(os.environ.get("MISTRAL_API_KEY") or ""),
            model=config.llm.mistral_model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
        )


class EmbeddingOllama(OllamaEmbeddings):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="http://localhost:11434", model=config.embeddings.model
        )


class EmbeddingMistral(Embeddings):
    """Mistral embeddings через официальный API"""

    def __init__(self, config: DictConfig):
        try:
            from mistralai import Mistral
        except ImportError:
            raise ImportError(
                "Для использования Mistral embeddings установите: pip install mistralai"
            )

        api_key = os.environ.get("MISTRAL_API_KEY") or ""
        if not api_key:
            raise ValueError("MISTRAL_API_KEY не установлен в переменных окружения")

        self.client = Mistral(api_key=api_key)
        self.model = "mistral-embed"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Встраивает список документов (с разбивкой на батчи)"""
        import time

        batch_size = 16
        all_embeddings = []

        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                embeddings_batch_response = self.client.embeddings.create(
                    model=self.model, inputs=batch
                )
                batch_embeddings = [
                    item.embedding for item in embeddings_batch_response.data
                ]
                all_embeddings.extend(batch_embeddings)

                if i + batch_size < len(texts):
                    time.sleep(0.1)

            return all_embeddings
        except Exception as e:
            raise Exception(f"Ошибка при получении embeddings от Mistral: {e}")

    def embed_query(self, text: str) -> List[float]:
        """Встраивает один запрос"""
        try:
            embeddings_batch_response = self.client.embeddings.create(
                model=self.model, inputs=[text]
            )
            return embeddings_batch_response.data[0].embedding
        except Exception as e:
            raise Exception(f"Ошибка при получении embedding от Mistral: {e}")


class LLMWorker:
    def __init__(self, config: DictConfig):
        llm_type = config.llm.type
        llm_map = {"mistral": LLMMistral, "deepseek": LLMDeepSeek}
        self.llm = llm_map.get(llm_type)(config)

        embeddings_type = getattr(config.embeddings, "type", None) or llm_type
        if embeddings_type == "mistral":
            self.embeddings = EmbeddingMistral(config)
        else:
            self.embeddings = EmbeddingOllama(config)

        self.history = []

    async def _run_llm(
        self, input: Dict[str, str], template: str, parser: Optional[Type[T]] = None
    ):
        prompt = ChatPromptTemplate.from_template(template)

        if parser:
            chain = RunnablePassthrough() | prompt | self.llm | parser
        else:
            chain = RunnablePassthrough() | prompt | self.llm
        return await chain.ainvoke(input)

    def _test_llm(self):
        return self.llm.invoke("Who are you?")

    async def get_entities_and_relations(self, text: str):
        parser = PydanticOutputParser(pydantic_object=EntitiesRelationships)
        input = {"text": text, "format_instructions": parser.get_format_instructions()}
        return await self._run_llm(
            input=input, template=FEATURE_EXTRACT_TEMPLATE, parser=parser
        )

    async def get_struct_from_query(self, query: str):
        parser = JsonOutputParser(
            schema={"type": "array", "items": Query.model_json_schema()}
        )
        input = {
            "query": query,
            "format_instructions": parser.get_format_instructions(),
        }
        return await self._run_llm(
            input=input, template=QUERY2GRAPH_TEMPLATE, parser=parser
        )

    async def get_canonical_names(self, names: list):
        parser = JsonOutputParser(
            schema={"type": "array", "items": CanonicalName.model_json_schema()}
        )
        input = {
            "names": names,
            "format_instructions": parser.get_format_instructions(),
        }
        return await self._run_llm(
            input=input, template=CANONICAL_NAMES_TEMPLATE, parser=parser
        )

    async def get_chapter_summary(self, chapter: str):
        input = {"chapter": chapter}
        return await self._run_llm(
            input=input, template=CHAPTER_SUMMARY_TEMPLATE, parser=StrOutputParser()
        )

    async def answer(self, query: str, context: str):
        input = {"context": context, "query": query}
        return await self._run_llm(input=input, template=ANSWER_TEMPLATE)
