UNWIND $nodes AS node
CALL apoc.create.node([node.label], node.properties)
YIELD node AS created
RETURN count(created) AS created_nodes