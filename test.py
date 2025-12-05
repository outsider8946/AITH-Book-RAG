from utils.db_loader import Neo4jLoader

loader = Neo4jLoader("/home/dolor/code/AITH-Book-RAG/monte_cristo_chapters")
loader._extract_nodes_and_realtions()
# print(loader.llm._test_llm())
