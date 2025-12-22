import re
import json
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from pathlib import Path
from neo4j import GraphDatabase

from utils.llm import LLMWorker
from utils.config_loader import config


class Neo4jLoader:
    def __init__(self, path2data: str = '', path2save: str = "./data/entities_and_relations_v2"):
        self.path2data = Path(path2data)
        self.path2save = Path(path2save)
        self.llm = LLMWorker(config)
        self.uri = 'neo4j://localhost:7687'
        self.username = 'neo4j'
        self.password = 'password123' 

    async def _precess_extract_nodes_and_edges(self, path2json, chapter):
        chapter_content = chapter.read_text(encoding="utf-8")
        entities_and_realations = await self.llm.get_entities_and_relations(chapter_content)
        json_data = entities_and_realations.model_dump_json(indent=4, ensure_ascii=False)
        path2json.write_text(json_data, encoding="utf-8")

    async def _extract_nodes_and_realtions(self):
        tasks = []
        self.path2save.mkdir(exist_ok=True)
        parts = [item for item in self.path2data.iterdir() if item.is_dir()]
        for part in tqdm(parts, total=len(parts), desc="parts"):
            chapters_path = part
            chapters = [item for item in chapters_path.iterdir() if item.is_file()]
            for chapter in tqdm(
                chapters, total=len(chapters), desc=f"chapters of {part.name}"
            ):
                file_name = f"{part.name}-{chapter.stem}.json"
                path2json = self.path2save / file_name
                tasks.append(self._precess_extract_nodes_and_edges(path2json, chapter))
        
        if len(tasks) > 0:
            await tqdm_asyncio.gather(*tasks, desc=f"Chapters of {part.name}")
        
    def _convert_nodes(self, nodes):
        query = ""
        params = {}

        nodes = self._canonical_nodes(nodes)
        nodes = self._merge_nodes(nodes)

        for node in nodes:
            name = node['name']
            name = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9]', '_', name).strip('_')
            params[name] = node
            query += f"""CREATE (:{node["entity_type"]} ${name})\n"""
        
        return (query, params)
            
    def _canonical_nodes(self, nodes):
        canonical_names_items = json.load(open('data/canonical_names.json'))['персонажи']
        unique_nodes = []
        for node in nodes:
            if node['entity_type'] in {'персонаж', 'person', 'персона'}:
                for item in canonical_names_items:
                    if node['name'].lower() in item['псевдонимы']:
                        node['name'] = item['каноническое_имя']
                        break
            unique_nodes.append(node)
        
        with open('./data/unqiue_nodes.json', 'w', encoding='utf-8') as f:
            json.dump(unique_nodes, f, indent=4, ensure_ascii=False)

        return unique_nodes
    
    def _merge_nodes(self, nodes):
        nodes_dict = {}
        for node in nodes:
            if node['name'] not in nodes_dict:
                nodes_dict[node['name']] = [node]
            else:
                nodes_dict[node['name']].append(node)
        
        merge_nodes = []

        for value in nodes_dict.values():
            #general_description = '\n'.join([item['description'] for item in value])
            merge_node = value[0]
            merge_node['description'] = value[0]['description']
            merge_nodes.append(merge_node)
        
        with open('./data/merge_nodes.json', 'w', encoding='utf-8') as f:
            json.dump(merge_nodes, f, indent=4, ensure_ascii=False)
        
        return merge_nodes
               
    
    def _convert_edges(self, edges: list):
        if not edges:
            return "", {}

        edge_data = []
        for edge in edges:
            rel_type = edge["relationship_type"]
            if not rel_type.replace("_", "").replace("-", "").isalnum() or not rel_type[0].isalpha():
                rel_type = f"`{rel_type}`"
            edge_data.append({
                "src_name": edge["entity_1"],
                "tgt_name": edge["entity_2"],
                "rel_type": rel_type,
                "description": edge.get("description", "")
            })

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

    def test_preprocessing_nodes(self):
        data_path = [
                '/home/dolor/code/AITH-Book-RAG/data/entities_and_relations_v2/Часть вторая-01_Контрабандисты.json',
                '/home/dolor/code/AITH-Book-RAG/data/entities_and_relations_v2/Часть вторая-02_Остров Монте-Кристо.json'
        ]
        nodes = []
        for path in data_path:
            temp_nodes = json.load(open(path))['entities']
            nodes.extend(temp_nodes)

        nodes = self._canonical_nodes(nodes)
        nodes = self._merge_nodes(nodes)
        
        return nodes
    
    def load2db(self):
        nodes = []
        edges = []
        files = [item for item in self.path2save.iterdir() if item.is_file()]
        for file in files:
            json_data = json.load(open(file))
            nodes.extend(json_data['entities'])
            edges.extend(json_data['relationships'])

        query_node, params_node = self._convert_nodes(nodes)
        query_edge, params_edge = self._convert_edges(edges)
        
        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            driver.execute_query("MATCH (n) DETACH DELETE n", database='neo4j')
            records, summary_node, keys = driver.execute_query(query_node, params_node, database='neo4j')
            records, summary_edge, keys = driver.execute_query(query_edge, params_edge, database='neo4j')
            return summary_node, summary_edge
    
    def test_extract_nodes_and_edges(self):
        path2save = Path('./data/test')
        path2save.mkdir(exist_ok=True)
        path = [Path('/home/dolor/code/AITH-Book-RAG/monte_cristo_chapters/Часть вторая/01_Контрабандисты.txt'),
                Path('/home/dolor/code/AITH-Book-RAG/monte_cristo_chapters/Часть вторая/02_Остров Монте-Кристо.txt'),
                Path('/home/dolor/code/AITH-Book-RAG/monte_cristo_chapters/Часть вторая/05_Трактир «Гарский мост».txt')
        ]

        for file in tqdm(path):
            text = file.read_text(encoding="utf-8")
            entities_and_realations = self.llm.get_entities_and_relations(text).model_dump_json(indent=4, ensure_ascii=False)
            with open(f'{path2save/file.stem}.json', "w", encoding="utf-8") as f:
                f.write(entities_and_realations)
    
    def _canonical_names(self):
        unqiue_names = set()
        json_files = [item for item in self.path2save.iterdir() if item.is_file()]
        nodes = []
        for file in json_files:
            json_item = json.load(open(file))
            nodes.extend(json_item['entities'])

        for node in nodes:
            if node['name'] not in unqiue_names and node['entity_type'] == 'персонаж':
                unqiue_names.add(node['name'])

        return list(unqiue_names)
    
        
        
