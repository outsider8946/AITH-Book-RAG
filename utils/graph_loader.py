import re
import json
from typing import List, Dict, Any
from pathlib import Path
from utils.llm import LLMWorker
from utils.config_loader import config
from tqdm.asyncio import tqdm_asyncio
from neo4j import GraphDatabase


class GrpahLoader:
    def __init__(
        self,
        path2data: str = "./book_data",
        path2save: str = "./data/entities_and_relations",
    ):
        self.llm = LLMWorker(config)
        self.path2data = Path(path2data)
        self.path2save = Path(path2save)

    async def _process_extract_nodes_and_edges(self, path2json: Path, chapter: Path):
        chapter_content = chapter.read_text(encoding="utf-8")
        entities_and_realations = await self.llm.get_entities_and_relations(
            chapter_content
        )
        json_data = entities_and_realations.model_dump_json(
            indent=4, ensure_ascii=False
        )
        path2json.write_text(json_data, encoding="utf-8")

    async def _extract_nodes_and_realtions(self):
        tasks = []
        self.path2save.mkdir(exist_ok=True)
        parts = [item for item in self.path2data.iterdir() if item.is_dir()]
        for part in parts:
            chapters_path = part
            chapters = [item for item in chapters_path.iterdir() if item.is_file()]
            for chapter in chapters:
                file_name = f"{part.name}-{chapter.stem}.json"
                path2json = self.path2save / file_name
                tasks.append(self._process_extract_nodes_and_edges(path2json, chapter))

        if len(tasks) > 0:
            await tqdm_asyncio.gather(
                *tasks, desc="Nodes and realtions extracting processing"
            )

    def _canonical_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.names_map = {}  # key - non-canonical name, value - canonical name
        names_map = json.load(open("data/names_map.json"))
        unique_nodes = []
        for node in nodes:
            if node["entity_type"] in {"персонаж", "person", "персона"}:
                for key, value in names_map.items():
                    if node["name"].lower() in value:
                        self.names_map[node["name"].lower()] = key
                        node["name"] = key
                        break
            unique_nodes.append(node)

        return unique_nodes

    def _merge_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        nodes_dict = {}
        for node in nodes:
            node["name"] = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", node["name"]).strip("_")
            if node["name"] not in nodes_dict:
                nodes_dict[node["name"]] = [node]
            else:
                nodes_dict[node["name"]].append(node)

        merge_nodes = []
        for value in nodes_dict.values():
            merge_node = value[0]
            merge_node["description"] = value[0]["description"]
            merge_nodes.append(merge_node)

        return merge_nodes

    def _normalize_edges(self, edges: List[Dict[str, str]]) -> List[Dict[str, str]]:
        for edge in edges:
            rel_type = edge["relationship_type"]
            if (
                not rel_type.replace("_", "").replace("-", "").isalnum()
                or not rel_type[0].isalpha()
            ):
                edge["relationship_type"] = f"`{rel_type}`"

            edge["entity_1"] = re.sub(
                r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                "_",
                self.names_map.get(edge["entity_1"], edge["entity_1"]),
            ).strip("_")
            edge["entity_2"] = re.sub(
                r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                "_",
                self.names_map.get(edge["entity_2"], edge["entity_2"]),
            ).strip("_")

        return edges

    async def create_graph(self):
        await self._extract_nodes_and_realtions()
        nodes = []
        edges = []
        files = [item for item in self.path2save.iterdir() if item.is_file()]
        for file in files:
            json_data = json.load(open(file))
            nodes.extend(json_data["entities"])
            edges.extend(json_data["relationships"])

        nodes = self._canonical_nodes(nodes)
        nodes = self._merge_nodes(nodes)

        edges = self._normalize_edges(edges)

        with open("./data/nodes.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(nodes, indent=4, ensure_ascii=False))

        with open("./data/edges.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(edges, indent=4, ensure_ascii=False))

    def load2db(self) -> None:
        nodes = json.load(open("./data/nodes.json"))
        edges = json.load(open("./data/edges.json"))

        query_node, params_node = self._load_nodes(nodes)
        query_edge, params_edge = self._load_edges(edges)

        with GraphDatabase.driver(
            "neo4j://localhost:7687", auth=("neo4j", "password123")
        ) as driver:
            driver.execute_query(self.cypher_loader.load("delete_db"), database="neo4j")
            driver.execute_query(query_node, params_node, database="neo4j")
            driver.execute_query(query_edge, params_edge, database="neo4j")
