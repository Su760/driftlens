import pytest

from driftlens.metrics.complexity import (
    ComplexityProfile,
    FunctionComplexity,
    analyze_complexity,
    compare_complexity,
    compute_complexity_profile,
    compute_gini,
)

CLEAN = "tests/fixtures/clean.py"
BLOATED = "tests/fixtures/bloated.py"


def test_gini_equal_values_is_zero():
    assert compute_gini([2.0, 2.0, 2.0, 2.0]) == 0.0


def test_gini_single_value_is_zero():
    assert compute_gini([5.0]) == 0.0


def test_gini_empty_is_zero():
    assert compute_gini([]) == 0.0


def test_gini_concentrated():
    # [0, 0, 0, 100] → Gini ≈ 0.75
    result = compute_gini([0.0, 0.0, 0.0, 100.0])
    assert abs(result - 0.75) < 1e-9


def test_gini_all_zeros_is_zero():
    assert compute_gini([0.0, 0.0, 0.0]) == 0.0


def test_gini_range():
    result = compute_gini([1.0, 4.0, 1.0, 7.0, 2.0])
    assert 0.0 <= result <= 1.0


def test_analyze_complexity_returns_all_functions():
    items = analyze_complexity(CLEAN)
    names = {item.name for item in items}
    assert {"add", "multiply", "factorial", "is_prime"} == names


def test_analyze_complexity_returns_function_complexity():
    items = analyze_complexity(CLEAN)
    assert all(isinstance(item, FunctionComplexity) for item in items)
    assert all(item.complexity >= 1 for item in items)


def test_analyze_complexity_ranks_are_valid():
    items = analyze_complexity(CLEAN)
    valid_ranks = set("ABCDEF")
    assert all(item.rank in valid_ranks for item in items)


def test_clean_vs_bloated_gini_not_higher():
    # Same logical complexity — Gini should be equal (both have same CC distribution)
    clean_profile = compute_complexity_profile(CLEAN)
    bloated_profile = compute_complexity_profile(BLOATED)
    assert clean_profile.gini <= bloated_profile.gini


def test_max_complexity_bloated():
    # factorial and is_prime each have CC=4; add and multiply have CC=1
    profile = compute_complexity_profile(BLOATED)
    assert profile.max_complexity == 4


def test_complexity_profile_fields():
    profile = compute_complexity_profile(CLEAN)
    assert isinstance(profile, ComplexityProfile)
    assert profile.function_count == 4
    assert profile.mean_complexity > 0
    assert 0.0 <= profile.gini <= 1.0


def test_empty_file_returns_zero_profile(tmp_path):
    empty = tmp_path / "empty.py"
    empty.write_text("")
    profile = compute_complexity_profile(str(empty))
    assert profile.gini == 0.0
    assert profile.max_complexity == 0
    assert profile.function_count == 0


def test_compare_complexity_positive_delta():
    assert compare_complexity(0.2, 0.5) == pytest.approx(0.3)


def test_compare_complexity_negative_delta():
    assert compare_complexity(0.5, 0.2) == pytest.approx(-0.3)


def test_compare_complexity_zero_delta():
    assert compare_complexity(0.4, 0.4) == 0.0
