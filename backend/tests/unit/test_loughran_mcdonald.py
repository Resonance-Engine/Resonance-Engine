"""Tests for Loughran-McDonald lexicon scorer."""

from src.nlp.loughran_mcdonald import load_lexicon, score_text


class TestLoadLexicon:
    def test_returns_all_categories(self):
        lexicon = load_lexicon()
        assert "positive" in lexicon
        assert "negative" in lexicon
        assert "uncertainty" in lexicon
        assert "litigious" in lexicon
        assert "constraining" in lexicon

    def test_categories_are_non_empty(self):
        lexicon = load_lexicon()
        for category, words in lexicon.items():
            assert len(words) > 0, f"Category '{category}' is empty"

    def test_words_are_lowercase(self):
        lexicon = load_lexicon()
        for category, words in lexicon.items():
            for word in words:
                assert word == word.lower(), f"'{word}' in '{category}' is not lowercase"


class TestScoreText:
    def test_negative_text(self):
        text = "The company faces bankruptcy and litigation due to fraud allegations."
        result = score_text(text)
        assert result["negative_count"] > 0
        assert result["net_sentiment"] < 0

    def test_positive_text(self):
        text = "Strong growth and profitable expansion with outstanding achievement."
        result = score_text(text)
        assert result["positive_count"] > 0
        assert result["net_sentiment"] > 0

    def test_uncertainty_detected(self):
        text = "We believe this could possibly indicate an uncertain outcome."
        result = score_text(text)
        assert result["uncertainty_count"] > 0

    def test_litigious_detected(self):
        text = "The defendant filed a complaint in court regarding the lawsuit."
        result = score_text(text)
        assert result["litigious_count"] > 0

    def test_empty_text(self):
        result = score_text("")
        assert result["total_words"] == 0
        assert result["net_sentiment"] == 0.0

    def test_neutral_text(self):
        text = "The cat sat on the mat."
        result = score_text(text)
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["net_sentiment"] == 0.0

    def test_returns_matching_words(self):
        text = "Strong growth amid decline and risk."
        result = score_text(text)
        assert "strong" in result["positive_words"] or "growth" in result["positive_words"]
        assert "decline" in result["negative_words"] or "risk" in result["negative_words"]

    def test_total_words_counted(self):
        text = "one two three four five"
        result = score_text(text)
        assert result["total_words"] == 5
