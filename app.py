from utils.db_loader import Neo4jLoader

loader = Neo4jLoader()
summary_node, summary_edge = loader.load2db()
print(f'SUMMARY NODE:\n {summary_node}')
print(f'SUMMARY EDGE:\n {summary_edge}')