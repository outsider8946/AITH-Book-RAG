import json
from utils.config_loader import config
from neo4j import GraphDatabase
from utils.llm import LLMWorker
from langchain_core.documents import Document
from langchain_community.vectorstores import Neo4jVector



class RAG:
    def __init__(self):
        self.llm = LLMWorker(config)
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    
    async def _extract_nodes_and_edges_from_query(self, query: str):
        json_query = await self.llm.get_struct_from_query(query)
        entities = json_query['entities']
        names_map = json.load(open('./data/names_map.json'))
        clear_entities = []
        for entity in entities:
            find = False
            for key, value in names_map.items():
                if entity.lower() in value:
                    clear_entities.append(key)
                    find = True
                    break

            if not find:    
                clear_entities.append(entity)
        
        json_query['entities'] = clear_entities

        return json_query
    
    def _graph_retrieve(self, json_query):
        with self.driver.session(database="neo4j") as session:
            result = session.run("""
            UNWIND $entities AS canon_name
            MATCH (start:person {name: canon_name})
                                 
            OPTIONAL MATCH (start)-[r]-(target)
            WITH start, r, target
            WHERE r IS NOT NULL
            RETURN 
              start.name AS source,
              type(r) AS rel_type,
              r.description AS rel_desc,
              target.name AS target,
              target.description AS tgt_desc
            """, entities=json_query['entities'], relations=json_query['relations'])

            documents = []
            for record in result:
                text = f"{record['source']} {record['rel_type']} {record['target']}. {record['rel_desc']}"
                documents.append(Document(page_content=text, metadata = {
                    "source": record['source'],
                    'target': record['target'],
                    'realtion': record['rel_type']
                }))
            return documents

    async def run(self, query):
        query_nodes_and_edges = await self._extract_nodes_and_edges_from_query(query)
        documents = self._graph_retrieve(query_nodes_and_edges)
        retriver = Neo4jVector.from_documents(
            documents,
            self.llm.embeddings,
            url="neo4j://localhost:7687",
            username="neo4j",
            password="password123"
        ).as_retriever(k=3)

        extracted_documents = retriver.invoke(query)
        context = '\n'.join([f"Действующее лицо: {doc.metadata['source']}\n Содержание: {doc.page_content}" for doc in extracted_documents])
        answer = await self.llm.answer(query=query, context=context)
        return answer.content
        
