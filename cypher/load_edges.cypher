UNWIND $edges AS edge
MATCH (a {name: edge.src_name})
MATCH (b {name: edge.tgt_name})
CALL apoc.create.relationship(a, edge.rel_type, {description: edge.description}, b)
YIELD rel
RETURN count(rel) AS created