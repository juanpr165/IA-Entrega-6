from orchestrator.tools import safe_calculate, sentiment_analysis


def test_safe_calculate_allows_math_only():
    assert safe_calculate("(10 + 5) * 2") == "30.0"
    assert "segura" in safe_calculate("__import__('os').system('x')")


def test_sentiment_is_traceable():
    result = sentiment_analysis("Me encanta este excelente resultado")
    assert result["sentiment"] == "positivo"
