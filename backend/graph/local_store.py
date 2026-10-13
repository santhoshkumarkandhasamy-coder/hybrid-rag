"""Knowledge graph stored in SQLite (used when Neo4j isn't configured).
Mirrors the function names of neo4j_store."""

from backend.core.db import get_conn


def create_document(document_id: str, filename: str):
    pass  # documents table already tracks this


def store_entities(document_id: str, entities: list[dict]):

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO graph_entities "
            "(document_id, name, type) VALUES (?, ?, ?)",
            [
                (document_id, e["name"], e.get("type", "CONCEPT"))
                for e in entities
            ],
        )


def store_relationships(document_id: str, relationships: list[dict]):

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO graph_relations "
            "(document_id, source, target, type) VALUES (?, ?, ?, ?)",
            [
                (document_id, r["source"], r["target"], r["type"])
                for r in relationships
            ],
        )


def get_document_graph(document_id: str) -> dict:

    with get_conn() as conn:
        entities = conn.execute(
            "SELECT name, type FROM graph_entities "
            "WHERE document_id = ? ORDER BY name",
            (document_id,),
        ).fetchall()

        relations = conn.execute(
            "SELECT r.source, s.type AS source_type, "
            "r.type AS relationship, r.target, t.type AS target_type "
            "FROM graph_relations r "
            "LEFT JOIN graph_entities s ON s.document_id = r.document_id "
            "  AND s.name = r.source "
            "LEFT JOIN graph_entities t ON t.document_id = r.document_id "
            "  AND t.name = r.target "
            "WHERE r.document_id = ? ORDER BY r.source, r.target",
            (document_id,),
        ).fetchall()

    return {
        "entities": [dict(e) for e in entities],
        "relationships": [dict(r) for r in relations],
    }


def search_graph(document_id: str, query: str, limit: int = 10):

    if not query.strip():
        raise ValueError("Graph search query cannot be empty.")

    terms = [t for t in query.lower().split() if len(t) > 2][:8]

    if not terms:
        return []

    like = " OR ".join(
        ["lower(r.source || ' ' || r.target) LIKE ?"] * len(terms)
    )
    params = [f"%{t}%" for t in terms]

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT r.source, s.type AS source_type, "
            "r.type AS relationship, r.target, t.type AS target_type "
            "FROM graph_relations r "
            "LEFT JOIN graph_entities s ON s.document_id = r.document_id "
            "  AND s.name = r.source "
            "LEFT JOIN graph_entities t ON t.document_id = r.document_id "
            "  AND t.name = r.target "
            f"WHERE r.document_id = ? AND ({like}) LIMIT 200",
            (document_id, *params),
        ).fetchall()

        lone = conn.execute(
            "SELECT name, type FROM graph_entities "
            "WHERE document_id = ? AND ("
            + " OR ".join(["lower(name) LIKE ?"] * len(terms))
            + ") LIMIT ?",
            (document_id, *params, limit),
        ).fetchall()

    scored = sorted(
        (dict(r) for r in rows),
        key=lambda r: -sum(
            t in f"{r['source']} {r['target']}".lower() for t in terms
        ),
    )[:limit]

    linked = {r["source"] for r in scored} | {r["target"] for r in scored}

    for ent in lone:
        if len(scored) >= limit:
            break
        if ent["name"] not in linked:
            scored.append(
                {
                    "source": ent["name"],
                    "source_type": ent["type"],
                    "relationship": None,
                    "target": None,
                    "target_type": None,
                }
            )

    return scored


def delete_document_graph(document_id: str):

    with get_conn() as conn:
        conn.execute(
            "DELETE FROM graph_entities WHERE document_id = ?",
            (document_id,),
        )
        conn.execute(
            "DELETE FROM graph_relations WHERE document_id = ?",
            (document_id,),
        )
