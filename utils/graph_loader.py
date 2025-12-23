import re
import json
from typing import List, Tuple, Dict, Any
from pathlib import Path
from neo4j import GraphDatabase
from utils.llm import LLMWorker
from utils.cypher_loader import CypherLoader
from utils.config_loader import config


class Neo4jLoader:
    def __init__(self) -> None:
        self.llm = LLMWorker(config)
        self.cypher_loader = CypherLoader()

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

        with open("./data/unqiue_nodes.json", "w", encoding="utf-8") as f:
            json.dump(unique_nodes, f, indent=4, ensure_ascii=False)

        return unique_nodes

    def _merge_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        nodes_dict = {}
        for node in nodes:
            if node["name"] not in nodes_dict:
                nodes_dict[node["name"]] = [node]
            else:
                nodes_dict[node["name"]].append(node)

        merge_nodes = []

        for value in nodes_dict.values():
            merge_node = value[0]
            merge_node["description"] = value[0]["description"]
            merge_nodes.append(merge_node)

        with open("./data/merge_nodes.json", "w", encoding="utf-8") as f:
            json.dump(merge_nodes, f, indent=4, ensure_ascii=False)

        return merge_nodes

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
                }
            )

        query = self.cypher_loader.load("load_edges")
        params = {"edges": edge_data}

        with open("./data/edges.json", "w", encoding="utf-8") as f:
            json.dump(edge_data, f, indent=4, ensure_ascii=False)

        return query, params

    def load2db(self, path2data: str = "./data/entities_and_relations_v2") -> None:
        nodes = []
        edges = []
        files = [item for item in Path(path2data).iterdir() if item.is_file()]
        for file in files:
            json_data = json.load(open(file))
            nodes.extend(json_data["entities"])
            edges.extend(json_data["relationships"])

        query_node, params_node = self._load_nodes(nodes)
        query_edge, params_edge = self._load_edges(edges)

        with GraphDatabase.driver(
            "neo4j://localhost:7687", auth=("neo4j", "password123")
        ) as driver:
            driver.execute_query(self.cypher_loader.load("delete_db"), database="neo4j")
            driver.execute_query(query_node, params_node, database="neo4j")
            driver.execute_query(query_edge, params_edge, database="neo4j")
