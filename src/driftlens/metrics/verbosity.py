"""Verbosity metric: measures how many lines a function uses per logical operation."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionVerbosity:
    name: str
    source_lines: int
    functional_units: int
    verbosity_ratio: float
    density: float  # functional_units per function — catches redundant operations


def _count_functional_units(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count meaningful logical operations in a function body."""
    count = 0
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            count += 1
        elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
            count += 1
        elif isinstance(child, ast.Return):
            count += 1
        elif isinstance(child, ast.If):
            count += 1
        elif isinstance(child, (ast.For, ast.While)):
            count += 1
    return max(count, 1)


def analyze_verbosity(filepath: str) -> list[FunctionVerbosity]:
    """Return per-function verbosity stats for every function/method in the file."""
    source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(source)

    results: list[FunctionVerbosity] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Total span: def line through last line of body (includes blank/comment lines)
            src_lines = node.end_lineno - node.lineno + 1
            src_lines = max(src_lines, 1)
            func_units = _count_functional_units(node)
            ratio = src_lines / func_units
            results.append(FunctionVerbosity(
                name=node.name,
                source_lines=src_lines,
                functional_units=func_units,
                verbosity_ratio=ratio,
                density=float(func_units),
            ))
    return results


def compute_verbosity(filepath: str) -> float:
    """Return the file-level average verbosity ratio across all functions.

    Higher values mean more lines are used per logical operation — a sign of bloat.
    Returns 0.0 if no functions are found.
    """
    results = analyze_verbosity(filepath)
    if not results:
        return 0.0
    avg_ratio = sum(r.verbosity_ratio for r in results) / len(results)
    avg_density = sum(r.density for r in results) / len(results)
    return (avg_ratio * 0.5) + (avg_density * 0.5)


def compare_verbosity(baseline_ratio: float, current_ratio: float) -> float:
    """Return percentage change from baseline to current.

    Positive → code has grown more verbose.
    Negative → code has become more concise.
    """
    if baseline_ratio == 0:
        return 0.0
    return (current_ratio - baseline_ratio) / baseline_ratio * 100
