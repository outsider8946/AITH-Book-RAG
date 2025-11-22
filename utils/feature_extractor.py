from utils.llm import LLMWorker
from utils.config_loader import config
from models import EntitiesRelationships, Entity, Relationship
from langchain_core.output_parsers import PydanticOutputParser

llm = LLMWorker(config)
text = open('/home/dolor/code/AITH-Book-RAG/monte_cristo_chapters/Часть первая/01_Марсель. Прибытие.txt').read()
print(llm.get_entities_and_relations(text))
print(llm._test_llm())

# model = EntitiesRelationships(
#     entities=[
#         Entity(name='entity 1', entity_type='entity 1 type', singular=False, description='entity 1 descr'),
#         Entity(name='entity 2', entity_type='entity 2 type', singular=False, description='entity 2 descr')
#     ],
#     relationships=[
#         Relationship(entity_1='entity 1', entity_2='entity 2', relationship_type='realtion btw entity 1 and entity 2', description='relation descr')
#     ]
# )

# print(model.model_dump())
# print('-'*20)
# print(PydanticOutputParser(pydantic_object=EntitiesRelationships).get_format_instructions())