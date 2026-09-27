from backend.graph.extractor import extract_graph_data
from backend.graph.neo4j_store import (
    create_document,
    store_entities,
    store_relationships,
)


def ingest_document_graph(
    document_id: str,
    filename: str,
    text: str,
) -> dict:

    if not text or not text.strip():
        raise ValueError(
            "Document text is empty."
        )

    # -----------------------------------------
    # 1. Extract entities and relationships
    # -----------------------------------------

    extracted = extract_graph_data(text)

    entities = extracted.get(
        "entities",
        [],
    )

    relationships = extracted.get(
        "relationships",
        [],
    )

    # -----------------------------------------
    # 2. Create document node
    # -----------------------------------------

    create_document(
        document_id=document_id,
        filename=filename,
    )

    # -----------------------------------------
    # 3. Store entities
    # -----------------------------------------

    store_entities(
        document_id=document_id,
        entities=entities,
    )

    # -----------------------------------------
    # 4. Store relationships
    # -----------------------------------------

    store_relationships(
        document_id=document_id,
        relationships=relationships,
    )

    # -----------------------------------------
    # 5. Return result
    # -----------------------------------------

    return {
        "entities": len(entities),
        "relationships": len(relationships),
    }
