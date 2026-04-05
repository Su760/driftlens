"""Structural similarity metric: fingerprint AST node-type/depth distributions."""

import ast
from pathlib import Path

# Fingerprint type alias: maps (node_type_name, depth) → count
Fingerprint = dict[tuple[str, int], int]


def _walk_depth(node: ast.AST, depth: int, counts: Fingerprint) -> None:
    """Recursively walk AST, counting each node type at its depth."""
    key = (type(node).__name__, depth)
    counts[key] = counts.get(key, 0) + 1
    for child in ast.iter_child_nodes(node):
        _walk_depth(child, depth + 1, counts)


def compute_fingerprint(filepath: str) -> Fingerprint:
    """Return a structural fingerprint for the file.

    The fingerprint maps (node_type, depth) tuples to occurrence counts.
    Example: {("FunctionDef", 1): 3, ("If", 2): 5, ("For", 3): 2}
    Depth 0 is the Module node itself.
    """
    source = Path(filepath).read_text()
    if not source.strip():
        return {}
    tree = ast.parse(source)
    counts: Fingerprint = {}
    _walk_depth(tree, 0, counts)
    return counts


def compute_structural_distance(fp_a: Fingerprint, fp_b: Fingerprint) -> float:
    """Return cosine distance between two fingerprints.

    Range: 0.0 (identical structure) to 1.0 (completely different).
    Two empty fingerprints → 0.0. One empty, one non-empty → 1.0.
    """
    if not fp_a and not fp_b:
        return 0.0
    if not fp_a or not fp_b:
        return 1.0

    keys = set(fp_a) | set(fp_b)
    vec_a = [fp_a.get(k, 0) for k in keys]
    vec_b = [fp_b.get(k, 0) for k in keys]

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a * a for a in vec_a) ** 0.5
    mag_b = sum(b * b for b in vec_b) ** 0.5

    if mag_a == 0 or mag_b == 0:
        return 1.0

    similarity = dot / (mag_a * mag_b)
    # Clamp to [0, 1] to guard against floating-point drift above 1.0
    return 1.0 - min(similarity, 1.0)


def compare_structure(baseline_fp: Fingerprint, current_fp: Fingerprint) -> float:
    """Return cosine distance between baseline and current fingerprints.

    0.0 → no structural drift. 1.0 → completely different structure.
    """
    return compute_structural_distance(baseline_fp, current_fp)
