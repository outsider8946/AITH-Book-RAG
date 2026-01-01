import re
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from utils.llm import LLMWorker
from utils.cypher_loader import CypherLoader
from utils.text_extractor import TextExtractor
from utils.config_loader import config
from tqdm.asyncio import tqdm_asyncio
from neo4j import GraphDatabase


class GrpahLoader:
    def __init__(
        self,
        path2data: str = "./data/structed_text",
        path2kg: str = "./data/entities_and_relations",
        path2summary: str = "./data/chapter_sumamries.json",
    ):
        self.llm = LLMWorker(config)
        self.path2data = Path(path2data)
        self.path2kg = Path(path2kg)
        self.path2summary = Path(path2summary)
        self.extractor = TextExtractor()
        self.cypher_loader = CypherLoader()

    async def _process_extract_nodes_and_edges(self, path2json: Path, chapter: Path):
        chapter_content = chapter.read_text(encoding="utf-8")
        entities_and_realations = await self.llm.get_entities_and_relations(
            chapter_content
        )
        json_data = entities_and_realations.model_dump()

        chapter_name = path2json.stem.split("_")[0]
        for edge in json_data["relationships"]:
            edge["chapter"] = chapter_name

        path2json.write_text(
            json.dumps(json_data, indent=4, ensure_ascii=False), encoding="utf-8"
        )

    async def _process_summary_chapters(self, chapter: Path, name: str):
        chapter_content = chapter.read_text(encoding="utf-8")
        chapter_name = name.split("_")[0]
        chapter_summary = await self.llm.get_chapter_summary(chapter_content)
        return {chapter_name: chapter_summary}

    async def _extract_nodes_and_realtions(self):
        tasks_extract = []
        tasks_summary = []
        self.path2kg.mkdir(exist_ok=True)
        parts = [item for item in self.path2data.iterdir() if item.is_dir()]
        for part in parts:
            chapters_path = part
            chapters = [item for item in chapters_path.iterdir() if item.is_file()]
            for chapter in chapters:
                file_name = f"{part.name}-{chapter.stem}.json"
                path2json = self.path2kg / file_name

                if not path2json.exists():
                    tasks_extract.append(
                        self._process_extract_nodes_and_edges(path2json, chapter)
                    )

                if not self.path2summary.exists():
                    tasks_summary.append(
                        self._process_summary_chapters(chapter, file_name)
                    )

        if len(tasks_extract) > 0:
            await tqdm_asyncio.gather(
                *tasks_extract, desc="Nodes and realtions extracting processing"
            )

        if len(tasks_summary) > 0:
            summary_result = await tqdm_asyncio.gather(
                *tasks_summary, desc="Chapters summaries processing"
            )

            with open(self.path2summary, "w", encoding="utf-8") as f:
                f.write(json.dumps(summary_result, indent=4, ensure_ascii=False))

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
            node["name"] = (
                re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", node["name"])
                .replace("__", "_")
                .strip("_")
            )
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

            edge["entity_1"] = (
                re.sub(
                    r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                    "_",
                    self.names_map.get(edge["entity_1"], edge["entity_1"]),
                )
                .replace("__", "_")
                .strip("_")
            )
            edge["entity_2"] = (
                re.sub(
                    r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                    "_",
                    self.names_map.get(edge["entity_2"], edge["entity_2"]),
                )
                .replace("__", "_")
                .strip("_")
            )

        return edges

    async def create_graph(self):
        await self._extract_nodes_and_realtions()
        nodes = []
        edges = []
        files = [item for item in self.path2kg.iterdir() if item.is_file()]
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

    def _load_nodes(
        self, nodes: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, List[Dict[str, Any]]]]:
        nodes = self._canonical_nodes(nodes)
        nodes = self._merge_nodes(nodes)

        node_data = []
        for node in nodes:
            clean_name = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9]", "_", node["name"]).strip("_")
            node_data.append(
                {
                    "label": node["entity_type"],
                    "properties": {
                        "name": clean_name,
                        "description": node.get("description", ""),
                        "singular": node.get("singular", True),
                    },
                }
            )

        query = self.cypher_loader.load("load_nodes")
        params = {"nodes": node_data}

        return query, params

    def _load_edges(
        self, edges: List[Dict[str, str]]
    ) -> Tuple[str, Dict[str, List[Dict[str, str]]]]:
        if not edges:
            return "", {}

        edge_data = []
        for edge in edges:
            rel_type = edge["relationship_type"]
            if (
                not rel_type.replace("_", "").replace("-", "").isalnum()
                or not rel_type[0].isalpha()
            ):
                rel_type = f"`{rel_type}`"

            src_name = re.sub(
                r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                "_",
                self.names_map.get(edge["entity_1"], edge["entity_1"]),
            ).strip("_")
            tgt_name = re.sub(
                r"[^a-zA-Zа-яА-ЯёЁ0-9]",
                "_",
                self.names_map.get(edge["entity_2"], edge["entity_2"]),
            ).strip("_")
            edge_data.append(
                {
                    "src_name": src_name,
                    "tgt_name": tgt_name,
                    "rel_type": rel_type,
                    "description": edge.get("description", ""),
                    "chapter": edge.get("chapter", ""),
                }
            )

        query = self.cypher_loader.load("load_edges")
        params = {"edges": edge_data}

        return query, params

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

    async def pipeline(self) -> None:
        self.extractor.extract("./data/monte-cristo.txt")
        await self.create_graph()
        self.load2db()
