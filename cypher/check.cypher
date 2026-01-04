MATCH (n) 
WHERE n:персонаж OR n:место OR n:предмет OR n:организация 
RETURN count(n) as count 
LIMIT 1