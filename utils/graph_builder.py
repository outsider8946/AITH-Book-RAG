from pathlib import Path
from utils.llm import LLMWorker
from utils.config_loader import config
from tqdm.asyncio import tqdm_asyncio


class GrpahBuilder:
    def __init__(
        self,
        path2data: str = "./book_data",
        path2save: str = "./data/entities_and_relations_v2",
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
