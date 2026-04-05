"""Naming consistency metric: convention violation rate across identifiers."""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
UPPER_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")


@dataclass
class NamingProfile:
    total_identifiers: int
    convention_counts: dict[str, int] = field(default_factory=dict)
    dominant_convention: str = ""
    violation_rate: float = 0.0
    avg_identifier_length: float = 0.0


def _classify(name: str) -> str:
    """Classify an identifier into a naming convention."""
    if SNAKE_CASE.match(name):
        return "snake_case"
    if UPPER_CASE.match(name):
        return "UPPER_CASE"
    if PASCAL_CASE.match(name):
        return "PascalCase"
    if CAMEL_CASE.match(name):
        return "camelCase"
    return "other"


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _extract_identifiers(tree: ast.AST) -> list[str]:
    """Extract all user-defined identifiers from an AST, skipping _ and dunders."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_dunder(node.name):
                names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id != "_" and not _is_dunder(node.id):
                names.append(node.id)
        elif isinstance(node, ast.arg):
            if node.arg != "_" and not _is_dunder(node.arg):
                names.append(node.arg)
    return names


def analyze_naming(filepath: str) -> NamingProfile:
    """Return a naming convention profile for all identifiers in the file."""
    source = Path(filepath).read_text()
    tree = ast.parse(source)
    identifiers = _extract_identifiers(tree)

    if not identifiers:
        return NamingProfile(total_identifiers=0)

    counts: dict[str, int] = {}
    for name in identifiers:
        conv = _classify(name)
        counts[conv] = counts.get(conv, 0) + 1

    dominant = max(counts, key=counts.get)  # type: ignore[arg-type]
    dominant_count = counts[dominant]
    violation_rate = (len(identifiers) - dominant_count) / len(identifiers)
    avg_length = sum(len(n) for n in identifiers) / len(identifiers)

    return NamingProfile(
        total_identifiers=len(identifiers),
        convention_counts=counts,
        dominant_convention=dominant,
        violation_rate=violation_rate,
        avg_identifier_length=avg_length,
    )


def compare_naming(baseline_profile: NamingProfile, current_profile: NamingProfile) -> float:
    """Return the violation rate delta (current - baseline).

    Positive → more naming violations (drift detected).
    Negative → naming became more consistent (improvement).
    """
    return current_profile.violation_rate - baseline_profile.violation_rate
