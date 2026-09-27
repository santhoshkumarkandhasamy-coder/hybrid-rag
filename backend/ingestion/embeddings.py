from langchain_huggingface import HuggingFaceEmbeddings


MODEL_NAME = "BAAI/bge-small-en-v1.5"


def get_embedding_model():
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