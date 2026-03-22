"""Loughran-McDonald lexicon — finance-specific sentiment word lists.

The standard general-purpose sentiment lexicons (VADER, etc.) misclassify
financial terms. E.g., "liability" is negative in general English but
neutral in finance. Loughran-McDonald was built specifically for 10-K filings.

Categories: positive, negative, uncertainty, litigious, constraining, superfluous.
"""


def load_lexicon() -> dict[str, set[str]]:
    """Load the Loughran-McDonald word lists.

    Returns dict with keys: positive, negative, uncertainty, litigious, constraining.

    TODO: Phase 0 deliverable
    - Download or bundle LM word lists
    - Parse into category → set[word] mapping
    - Cache after first load
    """
    raise NotImplementedError("LM lexicon loader — Phase 0 deliverable")


def score_text(text: str) -> dict:
    """Score text using Loughran-McDonald lexicon.

    Returns: {
        "positive_count": int,
        "negative_count": int,
        "uncertainty_count": int,
        "litigious_count": int,
        "net_sentiment": float  # (positive - negative) / total_words
    }

    TODO: Phase 0 deliverable
    """
    raise NotImplementedError("LM sentiment scoring — Phase 0 deliverable")
