"""Complexity concentration metric: Gini coefficient over cyclomatic complexity."""

from dataclasses import dataclass
from pathlib import Path

from radon.complexity import cc_rank, cc_visit


@dataclass
class FunctionComplexity:
    name: str
    complexity: int
    rank: str  # A–F per radon's scale


@dataclass
class ComplexityProfile:
    gini: float
    max_complexity: int
    mean_complexity: float
    function_count: int


def compute_gini(values: list[float]) -> float:
    """Return the Gini coefficient of a list of values.

    0.0 → perfectly uniform distribution (equal complexity everywhere).
    1.0 → all complexity concentrated in a single function.
    Returns 0.0 for empty or single-element lists.
    """
    n = len(values)
    if n <= 1:
        return 0.0
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    # Standard formula: G = (2 * Σ(i * x_i) - (n+1) * Σ(x_i)) / (n * Σ(x_i))
    # where i is 1-indexed rank in sorted order
    weighted = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2 * weighted - (n + 1) * total) / (n * total)


def analyze_complexity(filepath: str) -> list[FunctionComplexity]:
    """Return per-function cyclomatic complexity for every function/method."""
    source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    results = cc_visit(source)
    return [
        FunctionComplexity(
            name=r.name,
            complexity=r.complexity,
            rank=cc_rank(r.complexity),
        )
        for r in results
    ]


def compute_complexity_profile(filepath: str) -> ComplexityProfile:
    """Return an aggregate complexity profile for the file.

    A high Gini score means complexity is concentrated in a few functions —
    a common sign of AI-generated code that bolts logic onto existing scaffolding.
    """
    items = analyze_complexity(filepath)
    if not items:
        return ComplexityProfile(
            gini=0.0,
            max_complexity=0,
            mean_complexity=0.0,
            function_count=0,
        )
    complexities = [float(item.complexity) for item in items]
    return ComplexityProfile(
        gini=compute_gini(complexities),
        max_complexity=max(item.complexity for item in items),
        mean_complexity=sum(complexities) / len(complexities),
        function_count=len(items),
    )


def compare_complexity(baseline_gini: float, current_gini: float) -> float:
    """Return the absolute delta between baseline and current Gini scores.

    Positive → complexity is concentrating (drift detected).
    Negative → complexity is spreading out (improvement).
    """
    return current_gini - baseline_gini
