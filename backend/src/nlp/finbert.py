"""FinBERT sentiment classifier — financial domain sentiment analysis.

Uses ProsusAI/finbert from HuggingFace transformers.
Returns: positive/negative/neutral + confidence score.
"""


def classify_sentiment(text: str) -> dict:
    """Run FinBERT sentiment classification on financial text.

    Returns: {"label": "positive"|"negative"|"neutral", "score": float}

    TODO: Phase 0 deliverable
    - Load ProsusAI/finbert model (cache after first load)
    - Tokenize input text
    - Run inference
    - Return top label + score
    """
    raise NotImplementedError("FinBERT classifier — Phase 0 deliverable")


def classify_batch(texts: list[str]) -> list[dict]:
    """Batch sentiment classification for efficiency.

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("FinBERT batch classifier — Phase 0 deliverable")
