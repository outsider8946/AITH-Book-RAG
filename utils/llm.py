import os
from pydantic import BaseModel
from typing import Dict, Optional, Type, TypeVar
from pydantic import SecretStr
from omegaconf import DictConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from utils.templates import FEATURE_EXTRACT_TEMPLATE
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from models import EntitiesRelationships

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMOllama(ChatOllama):
    def __init__(self, config: DictConfig):
        super().__init__(
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            top_k=config.llm.top_k,
            top_p=config.llm.top_p,
            repeat_penalty=config.llm.repeat_penalty,
        )


class LLMOpenRouter(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=SecretStr(os.environ.get("LLM_API_KEY") or ""),
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
        )


class LLMDeepSeek(ChatOpenAI):
    def __init__(self, config: DictConfig):
        super().__init__(
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ.get("LLM_API_KEY") or ""),
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            presence_penalty=config.llm.repeat_penalty,
        )


class LLMWorker:
    def __init__(self, config: DictConfig):
        if config.llm.deepseek:
            self.llm = LLMDeepSeek(config)
        elif config.llm.local:
            self.llm = LLMOllama(config)
        else:
            self.llm = LLMOpenRouter(config)

        self.history = []

    def _run_llm(
        self, input: Dict[str, str], template: str, parser: Optional[Type[T]] = None
    ):
        prompt = ChatPromptTemplate.from_template(template)

        if parser:
            chain = RunnablePassthrough() | prompt | self.llm | parser
        else:
            chain = RunnablePassthrough() | prompt | self.llm
        return chain.invoke(input)

    def _test_llm(self):
        return self.llm.invoke("Who are you?")

    def get_entities_and_relations(self, text: str):
        parser = PydanticOutputParser(pydantic_object=EntitiesRelationships)
        input = {"text": text, "format_instructions": parser.get_format_instructions()}
        return self._run_llm(
            input=input, template=FEATURE_EXTRACT_TEMPLATE, parser=parser
        )
