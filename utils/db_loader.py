import json
from tqdm import tqdm
from pathlib import Path
from neo4j import GraphDatabase

from utils.llm import LLMWorker
from utils.config_loader import config


class Neo4jLoader:
    def __init__(self, path2data: str = None):
        self.path2data = path2data
        self.llm = LLMWorker(config)
        self.uri = 'neo4j://localhost:7687'
        self.username = 'neo4j'
        self.password = 'password123' 

    def _extract_nodes_and_realtions(self):
        save_path = Path("./data")
        save_path.mkdir(exist_ok=True)

        data_path = Path(self.path2data)
        parts = [item for item in data_path.iterdir() if item.is_dir()]
        for part in tqdm(parts, total=len(parts), desc="parts"):
            chapters_path = data_path / part
            chapters = [item for item in chapters_path.iterdir() if item.is_file()]
            for chapter in tqdm(
                chapters, total=len(chapters), desc=f"chapters of {part.name}"
            ):
                chapter_path = chapters_path / chapter
                chapter_content = chapter_path.read_text(encoding="utf-8")
                entities_and_realations = self.llm.get_entities_and_relations(
                    chapter_content
                ).model_dump_json(indent=4, ensure_ascii=False)
                file_name = f"{part.name}-{chapter.stem}.json"
                with open(save_path / file_name, "w", encoding="utf-8") as f:
                    f.write(entities_and_realations)
    
    def _convert_nodes(self, nodes):
        query = ""
        params = {}
        for node in nodes:
            name = node['name']
            name = name.replace(' ', '_')
            name = name.replace('-', '_')
            params[name] = node
            query += f"""CREATE (:{node["entity_type"]} ${name})\n"""
        
        return (query, params)
    
    def _convert_edges(self, edges: list):
        if not edges:
            return "", {}

        # Подготавливаем данные для UNWIND
        edge_data = []
        for edge in edges:
            rel_type = edge["relationship_type"]
            # Экранируем тип связи, если содержит недопустимые символы
            if not rel_type.replace("_", "").replace("-", "").isalnum() or not rel_type[0].isalpha():
                rel_type = f"`{rel_type}`"
            edge_data.append({
                "src_name": edge["entity_1"],
                "tgt_name": edge["entity_2"],
                "rel_type": rel_type,
                "description": edge.get("description", "")
            })

        # Единый запрос с UNWIND
        query = """
    UNWIND $edges AS edge
    MATCH (a {name: edge.src_name})
    MATCH (b {name: edge.tgt_name})
    CALL apoc.create.relationship(a, edge.rel_type, {description: edge.description}, b)
    YIELD rel
    RETURN count(rel) AS created
    """.strip()

        params = {"edges": edge_data}
        return query, params

    
    def load2db(self, data_path: str = None):
        if not data_path:
            data_path = '/home/dolor/code/AITH-Book-RAG/data/Часть вторая-01_Контрабандисты.json'
        
        json_data = json.load(open(data_path))
        entities = json_data['entities']
        edges = json_data['relationships']
        query_node, params_node = self._convert_nodes(entities)
        query_edge, params_edge = self._convert_edges(edges)
        
        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            driver.execute_query("MATCH (n) DETACH DELETE n", database="neo4j")
            records, summary_node, keys = driver.execute_query(query_node, params_node, database='neo4j')
            records, summary_edge, keys = driver.execute_query(query_edge, params_edge, database='neo4j')
            return summary_node, summary_edge
        
