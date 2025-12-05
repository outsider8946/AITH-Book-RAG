from tqdm import tqdm
from pathlib import Path
from utils.llm import LLMWorker
from utils.config_loader import config

class Neo4jLoader():
    def __init__(self, path2data: str, save_path: str = './data'):
        self.path2data = path2data
        self.llm = LLMWorker(config)
        self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True)
    
    def _extract_nodes_and_realtions(self):        
        data_path = Path(self.path2data)
        parts = [item for item in data_path.iterdir() if item.is_dir()]
        for part in tqdm(parts, total=len(parts), desc='parts'):
            chapters_path = data_path / part
            chapters = [item for item in chapters_path.iterdir() if item.is_file()]
            for chapter in tqdm(chapters, total=len(chapters), desc=f'chapters of {part.name}'):
                chapter_path = chapters_path / chapter
                chapter_content = chapter_path.read_text(encoding='utf-8')
                entities_and_realations = self.llm.get_entities_and_relations(chapter_content).model_dump_json(indent=4, ensure_ascii=False)
                file_name = f'{part.name}-{chapter.stem}.json'
                with open(self.save_path/file_name, 'w', encoding='utf-8') as f:
                    f.write(entities_and_realations)
    
    def _load2db(self):
        

        