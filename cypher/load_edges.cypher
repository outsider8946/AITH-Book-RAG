UNWIND $edges AS edge
MATCH (a {name: edge.src_name})
MATCH (b {name: edge.tgt_name})
CALL apoc.merge.relationship(
    a, 
    edge.rel_type, 
    {},
    {description: edge.description, chapter: edge.chapter},
    b,
    {description: edge.description, chapter: edge.chapter}
)
YIELD rel
RETURN count(rel) AS created