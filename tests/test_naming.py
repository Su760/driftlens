import pytest

from driftlens.metrics.naming import (
    NamingProfile,
    _classify,
    analyze_naming,
    compare_naming,
)

CLEAN = "tests/fixtures/clean.py"
BLOATED = "tests/fixtures/bloated.py"


def test_classify_snake_case():
    assert _classify("x_y_z") == "snake_case"
    assert _classify("my_var") == "snake_case"
    assert _classify("result") == "snake_case"


def test_classify_camel_case():
    assert _classify("myVar") == "camelCase"
    assert _classify("getValue") == "camelCase"


def test_classify_pascal_case():
    assert _classify("MyClass") == "PascalCase"
    assert _classify("HttpResponse") == "PascalCase"


def test_classify_upper_case():
    assert _classify("MAX_SIZE") == "UPPER_CASE"
    assert _classify("PI") == "UPPER_CASE"


def test_violation_rate_zero_for_all_snake():
    profile = analyze_naming(CLEAN)
    assert profile.violation_rate == 0.0
    assert profile.dominant_convention == "snake_case"


def test_violation_rate_positive_for_mixed(tmp_path):
    mixed = tmp_path / "mixed.py"
    mixed.write_text(
        "def myFunc():\n"
        "    someVar = 1\n"
        "    another_var = 2\n"
        "    YetAnother = 3\n"
    )
    profile = analyze_naming(str(mixed))
    assert profile.violation_rate > 0.0
    assert profile.total_identifiers >= 4


def test_dunders_are_skipped(tmp_path):
    code = tmp_path / "dunders.py"
    code.write_text(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.name = 'x'\n"
        "    def __repr__(self):\n"
        "        return self.name\n"
    )
    profile = analyze_naming(str(code))
    names_found = profile.total_identifiers
    # Should find: Foo, self (x2 from args), name (x1 store) — NOT __init__, __repr__
    assert names_found > 0
    # Verify no dunder counted by checking convention_counts
    # PascalCase for Foo, snake_case for self/name
    assert "other" not in profile.convention_counts or profile.convention_counts.get("other", 0) == 0


def test_underscore_skipped(tmp_path):
    code = tmp_path / "under.py"
    code.write_text("for _ in range(10):\n    x = 1\n")
    profile = analyze_naming(str(code))
    # _ should be skipped, only x counted
    assert profile.total_identifiers == 1


def test_compare_naming_positive_delta():
    base = NamingProfile(total_identifiers=10, violation_rate=0.1)
    curr = NamingProfile(total_identifiers=10, violation_rate=0.4)
    assert compare_naming(base, curr) == pytest.approx(0.3)


def test_compare_naming_negative_delta():
    base = NamingProfile(total_identifiers=10, violation_rate=0.5)
    curr = NamingProfile(total_identifiers=10, violation_rate=0.2)
    assert compare_naming(base, curr) == pytest.approx(-0.3)


def test_compare_naming_zero_delta():
    base = NamingProfile(total_identifiers=10, violation_rate=0.3)
    curr = NamingProfile(total_identifiers=10, violation_rate=0.3)
    assert compare_naming(base, curr) == 0.0


def test_empty_file_returns_zero_profile(tmp_path):
    empty = tmp_path / "empty.py"
    empty.write_text("")
    profile = analyze_naming(str(empty))
    assert profile.total_identifiers == 0
    assert profile.violation_rate == 0.0


def test_avg_identifier_length():
    profile = analyze_naming(CLEAN)
    assert profile.avg_identifier_length > 0
