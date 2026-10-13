import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# =========================================================
# Load .env from project root
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
)


# =========================================================
# Neo4j Configuration
# =========================================================

NEO4J_URI = os.getenv(
    "NEO4J_URI"
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME"
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD"
)

NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j",
)


# =========================================================
# Validate Configuration
# =========================================================

if not NEO4J_URI:
    raise ValueError(
        "NEO4J_URI is missing from .env"
    )

if not NEO4J_USERNAME:
    raise ValueError(
        "NEO4J_USERNAME is missing from .env"
    )

if not NEO4J_PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD is missing from .env"
    )


# =========================================================
# Neo4j Driver
# =========================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD,
    ),
)


# =========================================================
# Connection Test
# =========================================================

def verify_connection() -> bool:

    driver.verify_connectivity()

    return True


# =========================================================
# Create Document
# =========================================================

def create_document(
    document_id: str,
    filename: str,
):

    query = """
    MERGE (d:Document {
        document_id: $document_id
    })

    SET d.filename = $filename

    RETURN d
    """

    driver.execute_query(
        query,
        document_id=document_id,
        filename=filename,
        database_=NEO4J_DATABASE,
    )


# =========================================================
# Store Entities
# =========================================================

def store_entities(
    document_id: str,
    entities: list[dict],
):

    if not entities:
        return

    query = """
    MATCH (d:Document {
        document_id: $document_id
    })

    UNWIND $entities AS entity

    MERGE (e:Entity {
        name: entity.name
    })

    SET e.type = entity.type

    MERGE (d)-[:CONTAINS_ENTITY]->(e)
    """

    driver.execute_query(
        query,
        document_id=document_id,
        entities=entities,
        database_=NEO4J_DATABASE,
    )


# =========================================================
# Store Relationships
# =========================================================

def store_relationships(
    document_id: str,
    relationships: list[dict],
):

    if not relationships:
        return

    query = """
    UNWIND $relationships AS rel

    MATCH (source:Entity {
        name: rel.source
    })

    MATCH (target:Entity {
        name: rel.target
    })

    MERGE (
        source
    )-[r:RELATES_TO {
        document_id: $document_id,
        type: rel.type
    }]->(
        target
    )
    """

    driver.execute_query(
        query,
        document_id=document_id,
        relationships=relationships,
        database_=NEO4J_DATABASE,
    )


# =========================================================
# Get Complete Document Graph
# =========================================================

def get_document_graph(
    document_id: str,
) -> dict:

    entity_query = """
    MATCH (
        d:Document {
            document_id: $document_id
        }
    )-[:CONTAINS_ENTITY]->(e:Entity)

    RETURN
        e.name AS name,
        e.type AS type

    ORDER BY e.name
    """

    relationship_query = """
    MATCH (
        source:Entity
    )-[r:RELATES_TO {
        document_id: $document_id
    }]->(
        target:Entity
    )

    RETURN
        source.name AS source,
        source.type AS source_type,
        r.type AS relationship,
        target.name AS target,
        target.type AS target_type

    ORDER BY
        source.name,
        target.name
    """

    entity_records, _, _ = driver.execute_query(
        entity_query,
        document_id=document_id,
        database_=NEO4J_DATABASE,
    )

    relationship_records, _, _ = driver.execute_query(
        relationship_query,
        document_id=document_id,
        database_=NEO4J_DATABASE,
    )

    entities = [
        record.data()
        for record in entity_records
    ]

    relationships = [
        record.data()
        for record in relationship_records
    ]

    return {
        "entities": entities,
        "relationships": relationships,
    }


# =========================================================
# Graph Search
# =========================================================

def search_graph(
    document_id: str,
    query: str,
    limit: int = 10,
) -> list[dict]:

    if not query.strip():
        raise ValueError(
            "Graph search query cannot be empty."
        )

    search_term = query.strip().lower()

    cypher = """
    MATCH (
        d:Document {
            document_id: $document_id
        }
    )-[:CONTAINS_ENTITY]->(source:Entity)

    OPTIONAL MATCH (
        source
    )-[r:RELATES_TO {
        document_id: $document_id
    }]->(
        target:Entity
    )

    WHERE
        toLower(source.name) CONTAINS $search_term
        OR (
            target IS NOT NULL
            AND toLower(target.name) CONTAINS $search_term
        )
        OR (
            r IS NOT NULL
            AND toLower(r.type) CONTAINS $search_term
        )

    RETURN
        source.name AS source,
        source.type AS source_type,
        CASE
            WHEN r IS NOT NULL
            THEN r.type
            ELSE NULL
        END AS relationship,
        CASE
            WHEN target IS NOT NULL
            THEN target.name
            ELSE NULL
        END AS target,
        CASE
            WHEN target IS NOT NULL
            THEN target.type
            ELSE NULL
        END AS target_type

    LIMIT $limit
    """

    records, _, _ = driver.execute_query(
        cypher,
        document_id=document_id,
        search_term=search_term,
        limit=limit,
        database_=NEO4J_DATABASE,
    )

    return [
        record.data()
        for record in records
    ]


# =========================================================
# Delete Document Graph
# =========================================================

def delete_document_graph(
    document_id: str,
):

    driver.execute_query(
        """
        MATCH ()-[r:RELATES_TO {document_id: $document_id}]->()
        DELETE r
        """,
        document_id=document_id,
        database_=NEO4J_DATABASE,
    )

    driver.execute_query(
        """
        MATCH (d:Document {document_id: $document_id})
        DETACH DELETE d
        """,
        document_id=document_id,
        database_=NEO4J_DATABASE,
    )

    # Remove entities no longer referenced by any document
    driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE NOT (:Document)-[:CONTAINS_ENTITY]->(e)
        DETACH DELETE e
        """,
        database_=NEO4J_DATABASE,
    )
