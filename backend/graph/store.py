"""Pick the graph backend: Neo4j if configured, else local SQLite."""

from backend.core import config


def _impl():
    if config.USE_NEO4J:
        from backend.graph import neo4j_store as impl
    else:
        from backend.graph import local_store as impl
    return impl


def create_document(*a, **k):
    return _impl().create_document(*a, **k)


def store_entities(*a, **k):
    return _impl().store_entities(*a, **k)


def store_relationships(*a, **k):
    return _impl().store_relationships(*a, **k)


def get_document_graph(*a, **k):
    return _impl().get_document_graph(*a, **k)


def search_graph(*a, **k):
    return _impl().search_graph(*a, **k)


def delete_document_graph(*a, **k):
    return _impl().delete_document_graph(*a, **k)
