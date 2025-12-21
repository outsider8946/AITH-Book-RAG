from typing import List
from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str = Field(description="Название сущности(lowercase)")
    entity_type: str = Field(description="Тип сущности (lowercase and snake case)")
    singular: bool = Field(
        description="Является ли сущность единственной (true) или множественной (false)"
    )
    description: str = Field(
        description="Описание сущности в данном тексте",
        default=""
    )


class Relationship(BaseModel):
    entity_1: str = Field(description="Название сущности 1 (lowercase)")
    entity_2: str = Field(description="Название сущности 2 (lowercase)")
    relationship_type: str = Field(
        description="Тип связи между сущностями 1 and 2 на русском (lowercase and snake case)"
    )
    description: str = Field(
        description="Описание, как связь описана или представлена в данном тексте",
        default=""
    )


class EntitiesRelationships(BaseModel):
    entities: List[Entity] = Field(description="Список сущностей", default=[])
    relationships: List[Relationship] = Field(
        description="Список связей между сущностями", default=[]
    )


class CanonicalName(BaseModel):
    canonical_name: str = Field(description='Каноническое имя персонажа (наиболее популярное и узнаваемое)')
    alias: List[str] = Field(description='Список всех его псевдонимов и других названий из списка')
