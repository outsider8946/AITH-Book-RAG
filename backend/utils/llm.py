import os
from typing import Dict, Optional, Any, List
from pydantic import SecretStr
from omegaconf import DictConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from backend.utils.templates import (
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
from backend.utils.models import EntitiesRelationships, CanonicalName, Query

load_dotenv()


class LLMDeepSeek(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ.get("DEEPSEEK_API_KEY", "")),
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
            api_key=SecretStr(os.environ.get("MISTRAL_API_KEY", "")),
            model=config.llm.mistral_model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
        )


class EmbeddingOllama(OllamaEmbeddings):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
            model=config.embeddings.ollama_model_name,
        )


class LLMWorker:
    def __init__(self, config: DictConfig) -> None:
        llm_type = config.llm.type
        llm_map = {"mistral": LLMMistral, "deepseek": LLMDeepSeek}
        self.llm = llm_map.get(llm_type)(config)

        embeddings_type = config.embeddings.type
        embeddings_map = {"ollama": EmbeddingOllama}
        self.embeddings = embeddings_map.get(embeddings_type)(config)

        self.history = []

    async def _run_llm(
        self,
        input: Dict[str, str],
        template: str,
        parser: Optional[Any] = StrOutputParser(),
    ) -> Any:
        prompt = ChatPromptTemplate.from_template(template)
        chain = RunnablePassthrough() | prompt | self.llm | parser
        return await chain.ainvoke(input)

    async def get_entities_and_relations(self, text: str) -> Any:
        parser = PydanticOutputParser(pydantic_object=EntitiesRelationships)
        input = {"text": text, "format_instructions": parser.get_format_instructions()}
        return await self._run_llm(
            input=input, template=FEATURE_EXTRACT_TEMPLATE, parser=parser
        )

    async def get_struct_from_query(self, query: str):
        """Извлечение структуры из запроса пользователя"""
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

    async def get_canonical_names(self, names: list) -> Dict[str, List[str]]:
        """Получение канонических имен персонажей"""
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

    async def get_chapter_summary(self, chapter: str) -> str:
        """Получение суммаризации главы"""
        return await self._run_llm(
            input={"chapter": chapter}, template=CHAPTER_SUMMARY_TEMPLATE
        )

    async def answer(self, query: str, context: str) -> str:
        """Получение ответа на вопрос пользователя по данном контексту"""
        return await self._run_llm(
            input={"context": context, "query": query}, template=ANSWER_TEMPLATE
        )
