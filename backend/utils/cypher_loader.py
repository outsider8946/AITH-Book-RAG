from pathlib import Path


class CypherLoader:
    def __init__(self, base_path: str = "cypher"):
        self.base_path = Path(base_path)

    def load(self, name: str) -> str:
        """
        Загружает запрос из cypher/{name}.cypher
        Пример: loader.load("find_entities") → содержимое find_entities.cypher
        """
        path = self.base_path / f"{name}.cypher"
        if not path.exists():
            raise FileNotFoundError(f"Cypher query '{name}' not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            query = f.read().strip()

        return query
