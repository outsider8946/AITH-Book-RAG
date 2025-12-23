UNWIND $entities AS canon_name
MATCH (start:person {name: canon_name})
OPTIONAL MATCH (start)-[r]-(target)
WITH start, r, target
WHERE r IS NOT NULL
RETURN 
start.name AS source,
type(r) AS rel_type,
r.description AS rel_desc,
target.name AS target,
target.description AS tgt_desc