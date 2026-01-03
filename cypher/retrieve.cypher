UNWIND $entities AS canon_name
MATCH (start {name: canon_name})
WHERE start:персонаж OR start:место OR start:предмет OR start:организация 
OPTIONAL MATCH (start)-[r]-(target)
WITH start, r, target
WHERE r IS NOT NULL 
  AND r.description IS NOT NULL
  AND (r.rel_embedding IS NOT NULL OR r.desc_embedding IS NOT NULL)

WITH start, r, target,
    CASE WHEN r.desc_embedding IS NOT NULL AND $query_embedding IS NOT NULL
         THEN vector.similarity.cosine(r.desc_embedding, $query_embedding)
         ELSE 0.0
    END AS desc_similarity

WITH start, r, target, desc_similarity
UNWIND $edge_embeddings AS edge_embedding
WITH start, r, target, desc_similarity, edge_embedding,
    CASE WHEN r.rel_embedding IS NOT NULL
         THEN vector.similarity.cosine(r.rel_embedding, edge_embedding)
         ELSE 0.0
    END AS rel_similarity

WITH start, r, target, desc_similarity, edge_embedding, rel_similarity,
    (0.5 * desc_similarity + 0.5 * rel_similarity) AS combined_similarity

WITH start, r, target, desc_similarity,
     MAX(combined_similarity) AS max_combined_similarity

RETURN 
  start.name AS source,
  type(r) AS rel_type,
  r.description AS rel_desc,
  target.name AS target,
  target.description AS tgt_desc,
  max_combined_similarity AS similarity,
  desc_similarity,
  start.entity_type AS source_type,
  target.entity_type AS target_type,
  r.chapter AS chapter
ORDER BY max_combined_similarity DESC
LIMIT 10