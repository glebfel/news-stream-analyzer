CREATE CONSTRAINT entity_key_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.key IS UNIQUE;

CREATE INDEX entity_text_lower IF NOT EXISTS
FOR (e:Entity) ON (e.text);

CREATE INDEX entity_type IF NOT EXISTS
FOR (e:Entity) ON (e.type);
