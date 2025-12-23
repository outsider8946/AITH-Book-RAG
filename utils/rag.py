import re
import json
from typing import Dict, List, Any
from utils.config_loader import config
from neo4j import GraphDatabase
from utils.cypher_loader import CypherLoader
from utils.llm import LLMWorker
from langchain_core.documents import Document
from langchain_community.vectorstores import Neo4jVector


class RAG:
    def __init__(self):
        self.llm = LLMWorker(config)
        self.cypher_loader = CypherLoader()

    async def _extract_nodes_and_edges_from_query(
        self, query: str
    ) -> Dict[str, List[Any]]:
        json_query = await self.llm.get_struct_from_query(query)
        entities = json_query["entities"]
        names_map = json.load(open("./data/names_map.json"))
        clear_entities = []
        for entity in entities:
            find = False
            entity2clear = None
            for key, value in names_map.items():
                if entity.lower() in value:
                    entity2clear = key
                    find = True
                    break

            if not find:
                entity2clear = entity

            entity2clear = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", entity2clear).strip("_")
            clear_entities.append(entity2clear)

        json_query["entities"] = clear_entities

        return json_query

    def _graph_retrieve(self, json_query: Dict[str, List[Any]]) -> List[Document]:
        with GraphDatabase.driver(
            "neo4j://localhost:7687", auth=("neo4j", "password123")
        ) as driver:
            query = self.cypher_loader.load("retrieve")
            params = {"entities": json_query["entities"]}
            records, _, _ = driver.execute_query(query, params, database="neo4j")
            documents = []
            for record in records:
                text = f"{record['source']} {record['rel_type']} {record['target']}. {record['rel_desc']}"
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": record["source"],
                            "target": record["target"],
                            "realtion": record["rel_type"],
                        },
                    )
                )
            return documents

    async def run(self, query: str) -> str:
        query_nodes_and_edges = await self._extract_nodes_and_edges_from_query(query)
        print(query_nodes_and_edges)
        documents = self._graph_retrieve(query_nodes_and_edges)
        retriver = Neo4jVector.from_documents(
            documents,
            self.llm.embeddings,
            url="neo4j://localhost:7687",
            username="neo4j",
            password="password123",
        ).as_retriever(k=3)

        extracted_documents = retriver.invoke(query)
        context = "\n".join(
            [
                f"Действующее лицо: {doc.metadata['source']}\n Содержание: {doc.page_content}"
                for doc in extracted_documents
            ]
        )
        answer = await self.llm.answer(query=query, context=context)
        return answer.content
