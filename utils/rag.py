import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.config_loader import config
from neo4j import GraphDatabase
from utils.cypher_loader import CypherLoader
from utils.llm import LLMWorker
from langchain_core.documents import Document
from langchain_community.vectorstores import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class RAG:
    def __init__(
        self,
        neo4j_url: str = "neo4j://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password123",
        database: str = "neo4j",
    ):
        self.llm = LLMWorker(config)
        self.cypher_loader = CypherLoader()
        self.neo4j_url = neo4j_url
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self._names_map = None
        self._load_names_map()

    def _load_names_map(self):
        """Загружает карту имен из файла"""
        names_map_path = Path("./data/names_map.json")
        if names_map_path.exists():
            try:
                with open(names_map_path, "r", encoding="utf-8") as f:
                    self._names_map = json.load(f)
            except Exception as e:
                logger.warning(f"Не удалось загрузить names_map.json: {e}")
                self._names_map = {}
        else:
            logger.warning(
                "Файл names_map.json не найден. Работаем без канонизации имен."
            )
            self._names_map = {}

    def _canonicalize_entity(self, entity: str) -> str:
        """Преобразует имя сущности в каноническую форму"""
        if not self._names_map:
            return re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", entity).strip("_")

        for key, value in self._names_map.items():
            if entity.lower() in value:
                return re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", key).strip("_")

        return re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", entity).strip("_")

    def _check_graph_available(self) -> bool:
        """Проверяет, доступен ли граф и содержит ли он данные с правильными метками"""
        try:
            with GraphDatabase.driver(
                self.neo4j_url, auth=(self.neo4j_user, self.neo4j_password)
            ) as driver:
                records, _, _ = driver.execute_query(
                    "MATCH (n) WHERE n:персонаж OR n:место RETURN count(n) as count LIMIT 1",
                    database=self.database,
                )
                node_count = records[0]["count"] if records else 0
                has_data = node_count > 0
                if not has_data:
                    logger.info(
                        "Граф доступен, но не содержит данных с нужными метками. Работаем в режиме LLM диалога."
                    )
                return has_data
        except Exception as e:
            logger.warning(f"Граф недоступен: {e}. Работаем в режиме LLM диалога.")
            return False

    async def _extract_nodes_and_edges_from_query(
        self, query: str
    ) -> Dict[str, List[Any]]:
        """Извлекает сущности и связи из запроса с использованием LLM"""
        json_query = await self.llm.get_struct_from_query(query)
        logger.debug(f"LLM вернул структуру: {json_query}")

        entities = []

        if isinstance(json_query, list):
            for query_obj in json_query:
                if isinstance(query_obj, dict):
                    entity = query_obj.get("entity", "")
                    if entity:
                        entities.append(entity)
                elif hasattr(query_obj, "entity"):
                    if query_obj.entity:
                        entities.append(query_obj.entity)
        elif isinstance(json_query, dict):
            if "entities" in json_query:
                entities = json_query.get("entities", [])
            elif "entity" in json_query:
                entities = [json_query["entity"]] if json_query["entity"] else []

        logger.info(f"Извлечено сущностей из запроса: {entities}")

        clear_entities = [
            self._canonicalize_entity(entity) for entity in entities if entity
        ]
        logger.info(f"Канонизированные сущности: {clear_entities}")

        return {"entities": clear_entities}

    def _graph_retrieve(
        self, json_query: Dict[str, List[Any]]
    ) -> Tuple[List[Document], List[Dict[str, Any]]]:
        """
        Извлекает документы из графа Neo4j на основе сущностей.
        Возвращает кортеж: (документы, метаданные о найденных связях)
        """
        entities = json_query.get("entities", [])
        logger.info(f"Поиск в графе для сущностей: {entities}")

        with GraphDatabase.driver(
            self.neo4j_url, auth=(self.neo4j_user, self.neo4j_password)
        ) as driver:
            query = self.cypher_loader.load("retrieve")
            params = {"entities": entities}
            records, _, _ = driver.execute_query(query, params, database=self.database)

            logger.info(f"Найдено записей в графе: {len(records)}")

            documents = []
            graph_metadata = []

            for record in records:
                text = f"{record['source']} {record['rel_type']} {record['target']}. {record.get('rel_desc', '')}"
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": record["source"],
                            "target": record["target"],
                            "relation": record["rel_type"],
                            "rel_desc": record.get("rel_desc", ""),
                        },
                    )
                )
                graph_metadata.append(
                    {
                        "source": record["source"],
                        "target": record["target"],
                        "relation": record["rel_type"],
                        "description": record.get("rel_desc", ""),
                    }
                )

            return documents, graph_metadata

    async def run(
        self, query: str, chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Выполняет RAG запрос с поддержкой истории чата.
        Может работать как с графом (RAG режим), так и без него (простой LLM диалог).

        Args:
            query: Вопрос пользователя
            chat_history: История чата в формате [{"role": "user/assistant", "content": "..."}]

        Returns:
            Словарь с ответом и метаданными:
            {
                "answer": str,
                "graph_metadata": List[Dict],
                "entities_found": List[str],
                "context_used": List[str],
                "llm_context": List[str]
            }
        """
        graph_available = self._check_graph_available()

        if not graph_available:
            logger.info("Граф недоступен. Работаем в режиме LLM диалога.")

            system_message = (
                "Вы - помощник по роману 'Граф Монте-Кристо' Александра Дюма. "
                "Отвечайте на вопросы о романе на основе ваших знаний."
            )

            messages = [("system", system_message)]

            if chat_history:
                for msg in chat_history[-10:]:
                    role = "human" if msg["role"] == "user" else "ai"
                    messages.append((role, msg["content"]))

            messages.append(("human", query))

            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | self.llm.llm
            response = await chain.ainvoke({})

            return {
                "answer": response.content
                if hasattr(response, "content")
                else str(response),
                "graph_metadata": [],
                "entities_found": [],
                "context_used": [],
                "llm_context": [],
            }

        query_nodes_and_edges = await self._extract_nodes_and_edges_from_query(query)
        entities_found = query_nodes_and_edges.get("entities", [])

        documents, graph_metadata = self._graph_retrieve(query_nodes_and_edges)

        if not documents:
            context = "В базе знаний не найдено информации по данному вопросу."
            if chat_history:
                history_text = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in chat_history[-5:]]
                )
                context = f"{context}\n\nПредыдущий контекст разговора:\n{history_text}"

            answer = await self.llm.answer(query=query, context=context)
            return {
                "answer": answer.content,
                "graph_metadata": [],
                "entities_found": entities_found,
                "context_used": [],
                "llm_context": [],
            }

        vectorstore = Neo4jVector.from_documents(
            documents,
            self.llm.embeddings,
            url=self.neo4j_url,
            username=self.neo4j_user,
            password=self.neo4j_password,
            database=self.database,
        )

        retriever = vectorstore.as_retriever(k=3, search_type="similarity")
        extracted_documents = retriever.invoke(query)

        context_parts = []
        for doc in extracted_documents:
            context_parts.append(
                f"Действующее лицо: {doc.metadata.get('source', 'Неизвестно')}\n"
                f"Содержание: {doc.page_content}"
            )

        context = "\n\n".join(context_parts)

        if chat_history:
            history_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in chat_history[-5:]]
            )
            context = f"Предыдущий контекст разговора:\n{history_text}\n\nАктуальный контекст:\n{context}"

        answer = await self.llm.answer(query=query, context=context)

        return {
            "answer": answer.content,
            "graph_metadata": graph_metadata,
            "entities_found": entities_found,
            "context_used": [doc.page_content for doc in extracted_documents],
            "llm_context": context,
        }

    async def answer(
        self, query: str, chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Упрощенный метод для получения только ответа (для обратной совместимости).
        Использует метод run() и возвращает только текст ответа.
        """
        result = await self.run(query, chat_history)
        return result["answer"]
