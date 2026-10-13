import threading
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings


MODEL_NAME = "BAAI/bge-small-en-v1.5"


_lock = threading.Lock()


def get_embedding_model():
    with _lock:
        return _build_model()


@lru_cache(maxsize=1)
def _build_model():
    """
    Create and return the local HuggingFace
    embedding model.
    """

    model = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )

    return model