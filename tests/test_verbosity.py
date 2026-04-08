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


def test_bloated_demo_file():
    """Bloated code with pointless intermediates must score >= 1.5x clean."""
    clean_code = """\
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def factorial(n):
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
"""
    bloated_code = """\
def add(a, b):
    first_number = a
    second_number = b
    result = first_number + second_number
    return result

def multiply(a, b):
    first_operand = a
    second_operand = b
    product = first_operand * second_operand
    return product

def factorial(n):
    if n <= 1:
        base_case_result = 1
        return base_case_result
    result = 1
    start_value = 2
    end_value = n + 1
    for i in range(start_value, end_value):
        result = result * i
    return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(clean_code)
        clean_file = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(bloated_code)
        bloated_file = f.name
    try:
        clean_score = compute_verbosity(clean_file)
        bloated_score = compute_verbosity(bloated_file)
        assert bloated_score >= 1.5 * clean_score, (
            f"Expected bloated ({bloated_score:.2f}) >= 1.5 * clean ({clean_score:.2f})"
        )
    finally:
        os.unlink(clean_file)
        os.unlink(bloated_file)


def test_density_signal():
    """A function with redundant intermediates should have higher verbosity."""
    concise = "def add(a, b):\n    return a + b\n"
    verbose = "def add(a, b):\n    x = a\n    y = b\n    result = x + y\n    return result\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(concise)
        concise_file = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(verbose)
        verbose_file = f.name
    try:
        concise_score = compute_verbosity(concise_file)
        verbose_score = compute_verbosity(verbose_file)
        assert verbose_score > concise_score, (
            f"Expected verbose ({verbose_score:.2f}) > concise ({concise_score:.2f})"
        )
    finally:
        os.unlink(concise_file)
        os.unlink(verbose_file)


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
