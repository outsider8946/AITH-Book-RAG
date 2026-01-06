UNWIND $edges AS edge
MATCH (a {name: edge.src_name})
MATCH (b {name: edge.tgt_name})
CALL apoc.merge.relationship(
    a, 
    edge.rel_type, 
    {},
    {description: edge.description, rel_embedding: edge.rel_embedding, desc_embedding: edge.desc_embedding},
    b,
    {description: edge.description, rel_embedding: edge.rel_embedding, desc_embedding: edge.desc_embedding}
)
YIELD rel
RETURN count(rel) AS created