"""FinBERT sentiment classifier — financial domain-specific NLP.

Uses the ProsusAI/finbert model from HuggingFace for financial sentiment
classification (positive, negative, neutral).

The model is loaded lazily on first call and cached for subsequent calls.
"""

import logging
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"
MAX_LENGTH = 512

# Lazy-loaded model and tokenizer
_pipeline = None
# Guards the lazy load: two concurrent first calls must not both
# instantiate the ~400MB model (memory spike / potential OOM).
_load_lock = threading.Lock()


@dataclass
class SentimentResult:
    """Result of FinBERT sentiment classification."""

    label: str  # "positive", "negative", "neutral"
    score: float  # confidence 0-1
    positive: float
    negative: float
    neutral: float


def _get_pipeline():
    """Lazy-load the FinBERT pipeline. Cached after first call.

    Double-checked locking: the fast path avoids the lock once loaded;
    the slow path serializes concurrent first loads.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    with _load_lock:
        if _pipeline is not None:  # another thread finished the load
            return _pipeline

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
        except ImportError:
            raise ImportError(
                "transformers and torch are required for FinBERT. "
                "Install with: pip install transformers torch"
            )

        logger.info("Loading FinBERT model: %s", MODEL_NAME)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _pipeline = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            top_k=None,  # replaces deprecated return_all_scores=True
            truncation=True,
            max_length=MAX_LENGTH,
        )
        logger.info("FinBERT model loaded successfully")
        return _pipeline


def classify_sentiment(text: str) -> SentimentResult:
    """Classify financial sentiment of a single text.

    Args:
        text: Financial text (news headline, filing excerpt, etc.).
              Will be truncated to 512 tokens.

    Returns:
        SentimentResult with label, confidence, and per-class scores.
    """
    pipe = _get_pipeline()
    results = pipe(text[:2000])  # Pre-truncate to avoid tokenizer overhead

    # Normalize: [[{label, score}, ...]] (older transformers) vs
    # [{label, score}, ...] (top_k=None on newer versions)
    scores_list = results[0] if isinstance(results[0], list) else results
    scores = {item["label"]: item["score"] for item in scores_list}

    positive = scores.get("positive", 0.0)
    negative = scores.get("negative", 0.0)
    neutral = scores.get("neutral", 0.0)

    # Determine top label
    label = max(scores, key=scores.get)

    return SentimentResult(
        label=label,
        score=scores[label],
        positive=positive,
        negative=negative,
        neutral=neutral,
    )


async def classify_sentiment_async(text: str) -> SentimentResult:
    """Async wrapper for classify_sentiment.

    FinBERT forward passes are CPU-heavy (hundreds of ms) — calling the
    sync version inside an async agent blocks the event loop, stalling
    every concurrent pipeline and WebSocket heartbeat. This runs the
    inference in a worker thread instead.

    Args:
        text: Financial text (news headline, filing excerpt, etc.).

    Returns:
        SentimentResult with label, confidence, and per-class scores.
    """
    import asyncio

    return await asyncio.to_thread(classify_sentiment, text)


def classify_batch(texts: list[str], batch_size: int = 16) -> list[SentimentResult]:
    """Classify sentiment for a batch of texts.

    Args:
        texts: List of financial texts.
        batch_size: Number of texts to process in each model forward pass.

    Returns:
        List of SentimentResult, one per input text.
    """
    pipe = _get_pipeline()
    truncated = [t[:2000] for t in texts]

    results = []
    for i in range(0, len(truncated), batch_size):
        batch = truncated[i : i + batch_size]
        batch_results = pipe(batch)

        for scores_list in batch_results:
            scores = {item["label"]: item["score"] for item in scores_list}
            positive = scores.get("positive", 0.0)
            negative = scores.get("negative", 0.0)
            neutral = scores.get("neutral", 0.0)
            label = max(scores, key=scores.get)

            results.append(
                SentimentResult(
                    label=label,
                    score=scores[label],
                    positive=positive,
                    negative=negative,
                    neutral=neutral,
                )
            )

    return results
