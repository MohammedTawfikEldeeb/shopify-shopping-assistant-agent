from loguru import logger
from sentence_transformers import CrossEncoder

_model = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model


def rerank(query: str, documents: list[str], top_k: int = 10) -> list[tuple[int, float]]:
    if not documents:
        return []

    scores = _get_model().predict([(query, doc) for doc in documents])
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    ranked_top = ranked[:top_k]

    logger.info(
        "Reranker query={} candidates={} top_k={}",
        query,
        len(documents),
        top_k,
    )
    for rank, (idx, score) in enumerate(ranked_top, 1):
        snippet = documents[idx][:120] + ("..." if len(documents[idx]) > 120 else "")
        logger.info("  #{} score={:.4f} | {}", rank, score, snippet)

    return [(idx, float(score)) for idx, score in ranked_top]


def warmup() -> None:
    _get_model().predict([("warmup", "warmup")])