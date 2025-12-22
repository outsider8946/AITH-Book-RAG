import re
from utils.config_loader import config
from neo4j import GraphDatabase
from utils.llm import LLMWorker


class RAG:
    def __init__(self):
        self.llm = LLMWorker(config)
        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    
    async def _extract_entity_from_query(self, query: str):
        struct = await self.llm.get_entities_and_relations(query)
        query_nodes = struct.model_dump()['entities']
        # for query_node in query_nodes:
        #     query_node['name'] = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9]', '_', query_node['name']).strip('_')
        return query_nodes
    
    def _graph_retrieve(self, query_nodes):
        with self.driver.session(database="neo4j") as session:
        # Основной запрос: найди сущности + 1–2 хопа связей, с описаниями
            result = session.run("""
            UNWIND $entities AS query_entity
            MATCH (n)
            WHERE 
            toLower(n.name) CONTAINS query_entity 
            OR query_entity CONTAINS toLower(n.name)
            WITH DISTINCT n
            OPTIONAL MATCH path = (n)-[r*1..2]-(m)
            WHERE m:персонаж OR m:место OR m:объект OR m:событие
            WITH n, collect(DISTINCT {
            source: n.name,
            rel: [rel IN relationships(path) | type(rel)],
            target: m.name,
            src_desc: coalesce(n.description, ""),
            tgt_desc: coalesce(m.description, "")
            }) AS paths
            RETURN n.name AS name, n.description AS description, paths
            LIMIT 5
            """, entities=query_nodes)

            contexts = []
            for record in result:
                # Основная нода
                ctx = f"СУЩНОСТЬ: {record['name']}\nОПИСАНИЕ: {record['description'] or '—'}\nСВЯЗИ:\n"
                for p in record["paths"]:
                    rel_chain = " → ".join(p["rel"])
                    ctx += f"- {p['source']} —[{rel_chain}]→ {p['target']}\n"
                    if p["src_desc"]: ctx += f"  ({p['src_desc'][:80]}...)\n"
                    if p["tgt_desc"]: ctx += f"  ({p['tgt_desc'][:80]}...)\n"
                contexts.append(ctx.strip())
            
            return "\n\n".join(contexts) if contexts else "Релевантные сущности не найдены."

    async def run(self, query):
        query_nodes = await self._extract_entity_from_query(query)
        entity_names = [node["name"].lower() for node in query_nodes]
        print('NAMES:\n', entity_names)
        context = self._graph_retrieve(entity_names)
        print('CONTEXT:\n', context)
        answer = await self.llm.answer(query=query, context=context)
        print('ANSWER:\n', answer)
        
