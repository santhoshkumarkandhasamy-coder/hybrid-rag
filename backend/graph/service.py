from backend.core import config
from backend.graph.store import (
    create_document,
    store_entities,
    store_relationships,
)


def extract_graph_data(text: str) -> dict:
    if config.USE_OPENAI:
        from backend.graph.extractor import extract_graph_data as llm
        return llm(text)

    from backend.graph.local_extractor import extract_graph_data as local
    return local(text)


from backend.ingestion.chunker import split_text

MAX_GRAPH_WINDOWS = 10


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

    # Large documents are processed in windows so a single
    # LLM call never exceeds the context limit.
    entities = []
    relationships = []

    seen_entities = set()
    seen_relationships = set()

    for window in split_text(
        text,
        chunk_size=12000,
        chunk_overlap=0,
    )[:MAX_GRAPH_WINDOWS]:

        extracted = extract_graph_data(window)

        for entity in extracted.get("entities", []):

            key = (entity.get("name"), entity.get("type"))

            if entity.get("name") and key not in seen_entities:
                seen_entities.add(key)
                entities.append(entity)

        for rel in extracted.get("relationships", []):

            key = (
                rel.get("source"),
                rel.get("type"),
                rel.get("target"),
            )

            if all(key) and key not in seen_relationships:
                seen_relationships.add(key)
                relationships.append(rel)

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
