"""Tests for the GitHub PR comment module."""

from driftlens.github import COMMENT_MARKER, format_comment

SAMPLE_RESULTS = [
    {
        "filepath": "src/foo.py",
        "composite_score": 42.5,
        "verbosity_delta": 0.15,
        "structural_distance": 0.30,
        "complexity_gini_delta": 0.05,
        "naming_violation_rate": 0.10,
    },
    {
        "filepath": "src/bar.py",
        "composite_score": 12.0,
        "verbosity_delta": 0.02,
        "structural_distance": 0.10,
        "complexity_gini_delta": 0.01,
        "naming_violation_rate": 0.00,
    },
]


def test_comment_formatting_produces_valid_markdown():
    body = format_comment(SAMPLE_RESULTS, overall=30.0, threshold=40, passed=True)

    # Must contain the idempotency marker
    assert COMMENT_MARKER in body

    # Must be valid markdown table (header + separator + rows)
    assert "| File |" in body
    assert "|------|" in body

    # Must contain pass badge
    assert "PASS" in body

    # Must contain overall score
    assert "30.0" in body


def test_comment_includes_per_file_scores():
    body = format_comment(SAMPLE_RESULTS, overall=30.0, threshold=40, passed=True)

    assert "src/foo.py" in body
    assert "42.5" in body
    assert "src/bar.py" in body
    assert "12.0" in body


def test_comment_fail_badge_when_not_passed():
    body = format_comment(SAMPLE_RESULTS, overall=65.0, threshold=40, passed=False)
    assert "FAIL" in body
    assert "PASS" not in body


def test_comment_rows_sorted_by_score_descending():
    body = format_comment(SAMPLE_RESULTS, overall=30.0, threshold=40, passed=True)
    idx_foo = body.index("src/foo.py")
    idx_bar = body.index("src/bar.py")
    # foo has higher score (42.5) so it should appear first
    assert idx_foo < idx_bar
