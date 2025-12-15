// merge_kg.cypher
// Принимает параметр $kg: {entities: [...], relationships: [...]}
// Работает с ЛЮБЫМ JSON-файлом вашей структуры

UNWIND $kg.entities AS ent
MERGE (e:Entity {name: toLower(ent.name)})
  SET e.entity_type = ent.entity_type,
      e.singular = ent.singular,
      e.description = ent.description,
      e.source_file = $source_file  // ← полезно для отладки!

WITH $kg AS kg, $source_file AS sf
UNWIND kg.relationships AS rel

MATCH (a:Entity {name: toLower(rel.entity_1)})
MATCH (b:Entity {name: toLower(rel.entity_2)})

CALL apoc.create.relationship(
  a,
  replace(toUpper(rel.relationship_type), '_', ''),
  {description: rel.description, source_file: sf},
  b
) YIELD rel AS createdRel

RETURN 
  count(DISTINCT a) + count(DISTINCT b) AS nodes_touched,
  count(createdRel) AS rels_created