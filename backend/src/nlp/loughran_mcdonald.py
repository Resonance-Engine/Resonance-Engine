"""Loughran-McDonald lexicon — finance-specific sentiment word lists.

The standard general-purpose sentiment lexicons (VADER, etc.) misclassify
financial terms. E.g., "liability" is negative in general English but
neutral in finance. Loughran-McDonald was built specifically for 10-K filings.

Categories: positive, negative, uncertainty, litigious, constraining.

Word lists sourced from:
https://sraf.nd.edu/loughranmcdonald-master-dictionary/
"""

import logging
import re
from pathlib import Path

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

LM_MASTER_URL = "https://sraf.nd.edu/loughranmcdonald-master-dictionary/"
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"

# Module-level lexicon (populated by load_lexicon)
_lexicon: dict[str, set[str]] | None = None

# Core word lists — curated subset of the Loughran-McDonald Master Dictionary.
# The full dictionary has ~85k entries; these are the most impactful terms
# for 8-K/10-K sentiment scoring. When the full CSV is available locally,
# load_lexicon() will use that instead.
_BUILTIN_NEGATIVE = {
    "abandon", "abolished", "abrupt", "absence", "adverse", "adversely",
    "against", "aggravate", "allegations", "annul", "bankruptcy", "breach",
    "burden", "catastrophe", "caution", "cease", "claim", "closure",
    "collapse", "complaint", "concern", "conflicting", "contempt",
    "contrary", "conviction", "costly", "damage", "damages", "deadlock",
    "decline", "declined", "declining", "default", "defective", "deferral",
    "deficiency", "deficit", "delay", "delisted", "denial", "depressed",
    "deteriorate", "deteriorating", "detriment", "detrimental", "difficult",
    "difficulty", "diminish", "disadvantage", "disapproval", "disclaim",
    "discontinue", "discrepancy", "disrupt", "disruption", "dissolution",
    "distress", "doubt", "downgrade", "downturn", "drop", "erode",
    "erosion", "error", "escalate", "eviction", "exacerbate", "excessive",
    "exclusion", "fail", "failed", "failure", "fall", "felony", "fine",
    "fined", "forbid", "force", "foreclosure", "forfeit", "forfeiture",
    "fraud", "fraudulent", "halt", "hamper", "hardship", "harm", "harmful",
    "hazard", "impair", "impairment", "impediment", "inability", "inadequate",
    "incur", "indictment", "ineffective", "insolvent", "investigation",
    "involuntary", "jeopardize", "lack", "lapse", "layoff", "liable",
    "liquidate", "liquidation", "litigation", "loss", "losses", "misappropriate",
    "misconduct", "misleading", "misrepresent", "misstate", "negative",
    "negatively", "neglect", "noncompliance", "obstacle", "omission",
    "onerous", "oppose", "overdue", "penalty", "persist", "plea", "plummet",
    "poor", "preclude", "prejudice", "problem", "prohibit", "prosecution",
    "protest", "questioned", "recall", "recession", "reckless", "recourse",
    "redress", "reduction", "refusal", "regret", "reject", "relinquish",
    "reluctance", "remediation", "repossess", "resign", "resignation",
    "restate", "restatement", "restrict", "restructuring", "retract",
    "revoke", "risk", "sanction", "scandal", "scarcity", "severe",
    "shortage", "shortfall", "shutdown", "slump", "stagnant", "stagnation",
    "strain", "subpoena", "sue", "sued", "suffer", "summons", "suspend",
    "suspension", "terminate", "termination", "threat", "threaten",
    "trespass", "trouble", "unable", "uncertain", "underpayment",
    "underperform", "unfavorable", "unforeseen", "unlawful", "unpaid",
    "unprofitable", "unreliable", "unsatisfactory", "unstable",
    "unsuccessful", "untimely", "unwilling", "verdict", "violate",
    "violation", "volatile", "volatility", "vulnerability", "warn",
    "warning", "weak", "weaken", "worsen", "worst", "writedown", "writeoff",
}

_BUILTIN_POSITIVE = {
    "accomplish", "accomplishment", "achieve", "achievement", "advance",
    "advantage", "approval", "approve", "attractive", "award", "benefit",
    "beneficial", "best", "better", "boost", "breakthrough", "competent",
    "confidence", "constructive", "creative", "deliver", "desirable",
    "distinction", "efficiency", "empower", "enable", "enhance", "enjoy",
    "enthusiasm", "exceed", "excellent", "exceptional", "exciting",
    "expansion", "favorable", "gain", "generous", "great", "greater",
    "greatest", "grow", "growth", "ideal", "improve", "improved",
    "improvement", "increase", "incredible", "ingenuity", "innovate",
    "innovation", "innovative", "integrity", "leadership", "lucrative",
    "momentum", "opportunity", "optimal", "optimism", "optimistic",
    "outpace", "outperform", "outstanding", "overcome", "positive",
    "positively", "premium", "profitable", "profitability", "progress",
    "prominence", "prosper", "prosperity", "rebound", "record", "recover",
    "recovery", "remarkable", "reward", "robust", "satisfaction",
    "solid", "strength", "strengthen", "strong", "succeed", "success",
    "successful", "superior", "surpass", "thrive", "transform",
    "tremendous", "upgrade", "upturn", "valuable", "win", "winner",
}

_BUILTIN_UNCERTAINTY = {
    "almost", "ambiguity", "ambiguous", "anticipate", "apparent",
    "approximately", "assume", "assumption", "believe", "cautious",
    "conceivable", "conditional", "contingency", "contingent", "could",
    "depend", "depending", "doubt", "estimate", "estimated", "expect",
    "expose", "fluctuate", "forecast", "hope", "if", "imprecise",
    "indefinite", "indicate", "likelihood", "may", "might", "nearly",
    "nonassessable", "occasionally", "pending", "perceive", "perhaps",
    "possibility", "possible", "possibly", "predict", "preliminary",
    "presume", "probabilistic", "probability", "probable", "probably",
    "project", "projected", "prospect", "random", "reassess", "recalculate",
    "reconsider", "reexamine", "reinterpret", "revise", "risk", "risky",
    "roughly", "rumor", "seem", "seldom", "sometime", "somewhat",
    "speculate", "speculative", "suggest", "susceptible", "tentative",
    "uncertain", "uncertainty", "unclear", "unconfirmed", "undecided",
    "undefined", "undetermined", "unforeseeable", "unknown", "unlikely",
    "unpredictable", "unproven", "unquantifiable", "unsettled", "unsure",
    "unusual", "variable", "vary",
}

_BUILTIN_LITIGIOUS = {
    "acquit", "adjudicate", "allegation", "allege", "alleged", "amicus",
    "appeal", "arbitrate", "arbitration", "attorney", "claimant", "class",
    "complaint", "consent", "counterclaim", "court", "crossclaim",
    "damages", "decree", "defendant", "deposition", "discovery",
    "dismiss", "docket", "enforce", "enforcement", "enjoin", "felony",
    "filing", "fine", "guilty", "hearing", "imprisonment", "indict",
    "indictment", "infraction", "infringe", "injunction", "inquiry",
    "investigate", "investigation", "judgment", "judicial", "jurisdiction",
    "jury", "law", "lawsuit", "lawyer", "legal", "legislate", "liable",
    "litigate", "litigation", "magistrate", "mediate", "misconduct",
    "misdemeanor", "motion", "notified", "offend", "order", "penalty",
    "petition", "plaintiff", "plead", "plea", "precedent", "proceeding",
    "prosecute", "prosecution", "regulator", "regulatory", "remand",
    "remedy", "respondent", "restitution", "rule", "ruling", "sanction",
    "sentence", "settle", "settlement", "statute", "subpoena", "sue",
    "suit", "summon", "testimony", "tort", "trial", "tribunal",
    "verdict", "violate", "violation", "witness",
}

_BUILTIN_CONSTRAINING = {
    "abide", "binding", "bound", "clause", "commitment", "compel",
    "compliance", "comply", "condition", "conform", "consent",
    "covenant", "curtail", "deadline", "decree", "directive",
    "duty", "encumber", "enforce", "forbid", "impede", "impose",
    "injunction", "instruction", "limit", "limitation", "mandate",
    "must", "necessitate", "obligate", "obligation", "oblige",
    "preclude", "prerequisite", "prescribe", "prohibit", "prohibition",
    "require", "required", "requirement", "restrict", "restricted",
    "restriction", "restrain", "shall", "stipulate",
}


def load_lexicon(csv_path: str | None = None) -> dict[str, set[str]]:
    """Load the Loughran-McDonald word lists.

    If a local CSV of the full master dictionary is available, loads from that.
    Otherwise uses the curated built-in word lists.

    Args:
        csv_path: Optional path to the LM Master Dictionary CSV.

    Returns:
        Dict with keys: positive, negative, uncertainty, litigious, constraining.
        Each value is a set of lowercase words.
    """
    global _lexicon

    if _lexicon is not None and csv_path is None:
        return _lexicon

    if csv_path is not None:
        _lexicon = _load_from_csv(csv_path)
    else:
        _lexicon = {
            "positive": _BUILTIN_POSITIVE,
            "negative": _BUILTIN_NEGATIVE,
            "uncertainty": _BUILTIN_UNCERTAINTY,
            "litigious": _BUILTIN_LITIGIOUS,
            "constraining": _BUILTIN_CONSTRAINING,
        }

    total = sum(len(v) for v in _lexicon.values())
    logger.info("Loaded LM lexicon: %d total words across %d categories", total, len(_lexicon))
    return _lexicon


def _load_from_csv(csv_path: str) -> dict[str, set[str]]:
    """Load the full Loughran-McDonald Master Dictionary from CSV."""
    import csv

    lexicon = {
        "positive": set(),
        "negative": set(),
        "uncertainty": set(),
        "litigious": set(),
        "constraining": set(),
    }

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("Word", "").lower()
            if not word:
                continue
            # In the LM CSV, non-zero values indicate category membership
            if int(row.get("Negative", "0") or 0) != 0:
                lexicon["negative"].add(word)
            if int(row.get("Positive", "0") or 0) != 0:
                lexicon["positive"].add(word)
            if int(row.get("Uncertainty", "0") or 0) != 0:
                lexicon["uncertainty"].add(word)
            if int(row.get("Litigious", "0") or 0) != 0:
                lexicon["litigious"].add(word)
            if int(row.get("Constraining", "0") or 0) != 0:
                lexicon["constraining"].add(word)

    return lexicon


def score_text(text: str) -> dict:
    """Score text using Loughran-McDonald lexicon.

    Args:
        text: Financial text to analyze.

    Returns:
        Dict with word counts per category plus net sentiment score.
    """
    lexicon = load_lexicon()

    # Tokenize: lowercase, strip punctuation, split on whitespace
    words = re.findall(r"[a-z]+", text.lower())
    total_words = len(words)

    if total_words == 0:
        return {
            "positive_count": 0,
            "negative_count": 0,
            "uncertainty_count": 0,
            "litigious_count": 0,
            "constraining_count": 0,
            "total_words": 0,
            "net_sentiment": 0.0,
            "positive_words": [],
            "negative_words": [],
        }

    pos_words = []
    neg_words = []
    counts = {cat: 0 for cat in lexicon}

    for word in words:
        for category, word_set in lexicon.items():
            if word in word_set:
                counts[category] += 1
                if category == "positive":
                    pos_words.append(word)
                elif category == "negative":
                    neg_words.append(word)

    net_sentiment = (counts["positive"] - counts["negative"]) / total_words

    return {
        "positive_count": counts["positive"],
        "negative_count": counts["negative"],
        "uncertainty_count": counts["uncertainty"],
        "litigious_count": counts["litigious"],
        "constraining_count": counts["constraining"],
        "total_words": total_words,
        "net_sentiment": round(net_sentiment, 6),
        "positive_words": list(set(pos_words)),
        "negative_words": list(set(neg_words)),
    }
