from fastembed import TextEmbedding

_model = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def embed_query(query: str) -> list[float]:
    embeddings = list(_get_model().query_embed(query))
    return embeddings[0].tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    embeddings = list(_get_model().passage_embed(texts))
    return [e.tolist() for e in embeddings]
