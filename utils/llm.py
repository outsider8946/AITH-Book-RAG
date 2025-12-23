import os
from pydantic import BaseModel
from typing import Dict, Optional, Type, TypeVar
from pydantic import SecretStr
from omegaconf import DictConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from utils.templates import (
    FEATURE_EXTRACT_TEMPLATE,
    CANONICAL_NAMES_TEMPLATE,
    ANSWER_TEMPLATE,
    QUERY2GRAPH_TEMPLATE,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from models import EntitiesRelationships, CanonicalName, Query

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMDeepSeek(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ.get("LLM_API_KEY") or ""),
            model=config.llm.model_name,
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
            api_key=SecretStr(os.environ.get("LLM_API_KEY") or ""),
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
        )


class EmbeddingOllama(OllamaEmbeddings):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="http://localhost:11434", model=config.embeddings.model
        )


class LLMWorker:
    def __init__(self, config: DictConfig):
        llm_type = config.llm.type
        llm_map = {"mistral": LLMMistral, "deepseek": LLMDeepSeek}
        self.llm = llm_map.get(llm_type)(config)
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

    async def answer(self, query: str, context: str):
        input = {"context": context, "query": query}
        return await self._run_llm(input=input, template=ANSWER_TEMPLATE)
