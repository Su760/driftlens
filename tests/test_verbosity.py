import os
import tempfile

import pytest

from driftlens.metrics.verbosity import (
    FunctionVerbosity,
    analyze_verbosity,
    compare_verbosity,
    compute_verbosity,
)

CLEAN = "tests/fixtures/clean.py"
BLOATED = "tests/fixtures/bloated.py"


def test_clean_lower_than_bloated():
    clean = compute_verbosity(CLEAN)
    bloated = compute_verbosity(BLOATED)
    assert clean < bloated, f"Expected clean ({clean:.2f}) < bloated ({bloated:.2f})"


def test_compare_verbosity_positive_delta():
    clean = compute_verbosity(CLEAN)
    bloated = compute_verbosity(BLOATED)
    delta = compare_verbosity(clean, bloated)
    assert delta > 0, f"Expected positive delta, got {delta:.1f}%"


def test_compare_verbosity_zero_delta():
    assert compare_verbosity(2.5, 2.5) == 0.0


def test_compare_verbosity_negative_delta():
    delta = compare_verbosity(3.0, 2.0)
    assert delta < 0


def test_compare_verbosity_zero_baseline():
    assert compare_verbosity(0.0, 5.0) == 0.0


def test_analyze_returns_function_verbosity():
    results = analyze_verbosity(CLEAN)
    assert len(results) > 0
    assert all(isinstance(r, FunctionVerbosity) for r in results)


def test_analyze_returns_all_functions():
    results = analyze_verbosity(CLEAN)
    names = {r.name for r in results}
    assert {"add", "multiply", "factorial", "is_prime"} == names


def test_empty_function():
    code = "def empty_func():\n    pass\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmpfile = f.name
    try:
        results = analyze_verbosity(tmpfile)
        assert len(results) == 1
        assert results[0].verbosity_ratio >= 1.0
    finally:
        os.unlink(tmpfile)


def test_single_line_function():
    code = "def add(a, b): return a + b\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmpfile = f.name
    try:
        results = analyze_verbosity(tmpfile)
        assert len(results) == 1
        assert results[0].source_lines == 1
    finally:
        os.unlink(tmpfile)


def test_class_methods():
    code = """\
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        result = a * b
        return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmpfile = f.name
    try:
        results = analyze_verbosity(tmpfile)
        names = {r.name for r in results}
        assert "add" in names
        assert "multiply" in names
    finally:
        os.unlink(tmpfile)
