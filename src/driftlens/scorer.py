"""Composite drift scorer: combines all four metrics into a single 0-100 score."""

from dataclasses import dataclass, field
from pathlib import Path

from driftlens.metrics.complexity import compare_complexity, compute_complexity_profile
from driftlens.metrics.naming import analyze_naming, compare_naming
from driftlens.metrics.structure import compare_structure, compute_fingerprint
from driftlens.metrics.verbosity import compute_verbosity


@dataclass
class DriftResult:
    composite_score: float
    verbosity_delta: float
    structural_distance: float
    complexity_gini_delta: float
    naming_violation_rate: float
    per_file_scores: list[dict] = field(default_factory=list)
    severity: str = "healthy"


def _severity(score: float) -> str:
    if score <= 15:
        return "healthy"
    if score <= 35:
        return "mild"
    if score <= 60:
        return "significant"
    return "critical"


def _relative_path(filepath: Path, base_dir: Path) -> str:
    return str(filepath.relative_to(base_dir))


def compute_drift(baseline_dir: str, current_dir: str) -> DriftResult:
    """Compare two directory snapshots and return a composite drift score.

    Scans all .py files in current_dir, computes deltas against baseline_dir.
    New files get max structural drift (1.0). Deleted files are skipped.
    """
    base_path = Path(baseline_dir)
    curr_path = Path(current_dir)

    baseline_files = {_relative_path(f, base_path) for f in base_path.rglob("*.py")}
    current_files = {_relative_path(f, curr_path) for f in curr_path.rglob("*.py")}

    per_file: list[dict] = []

    for rel in current_files:
        curr_file = str(curr_path / rel)

        if rel in baseline_files:
            base_file = str(base_path / rel)

            # Verbosity
            base_verb = compute_verbosity(base_file)
            curr_verb = compute_verbosity(curr_file)
            verb_delta = (curr_verb - base_verb) / base_verb if base_verb else 0.0

            # Structure
            base_fp = compute_fingerprint(base_file)
            curr_fp = compute_fingerprint(curr_file)
            struct_dist = compare_structure(base_fp, curr_fp)

            # Complexity
            base_profile = compute_complexity_profile(base_file)
            curr_profile = compute_complexity_profile(curr_file)
            comp_delta = compare_complexity(base_profile.gini, curr_profile.gini)

            # Naming
            base_naming = analyze_naming(base_file)
            curr_naming = analyze_naming(curr_file)
            naming_vr = compare_naming(base_naming, curr_naming)
        else:
            # New file — no baseline to compare against
            curr_verb = compute_verbosity(curr_file)
            verb_delta = curr_verb if curr_verb else 0.0
            struct_dist = 1.0
            curr_profile = compute_complexity_profile(curr_file)
            comp_delta = curr_profile.gini
            curr_naming = analyze_naming(curr_file)
            naming_vr = curr_naming.violation_rate

        per_file.append({
            "filepath": rel,
            "verbosity_delta": verb_delta,
            "structural_distance": struct_dist,
            "complexity_gini_delta": comp_delta,
            "naming_violation_rate": naming_vr,
        })

    if not per_file:
        return DriftResult(
            composite_score=0.0,
            verbosity_delta=0.0,
            structural_distance=0.0,
            complexity_gini_delta=0.0,
            naming_violation_rate=0.0,
            severity="healthy",
        )

    # Average across files
    avg_verb = sum(f["verbosity_delta"] for f in per_file) / len(per_file)
    avg_struct = sum(f["structural_distance"] for f in per_file) / len(per_file)
    avg_comp = sum(f["complexity_gini_delta"] for f in per_file) / len(per_file)
    avg_naming = sum(f["naming_violation_rate"] for f in per_file) / len(per_file)

    # Composite formula — clamp components to [0, 1] before weighting
    score = (
        0.30 * min(max(avg_verb, 0.0), 1.0)
        + 0.30 * min(max(avg_struct, 0.0), 1.0)
        + 0.25 * min(max(avg_comp * 2, 0.0), 1.0)
        + 0.15 * min(max(avg_naming, 0.0), 1.0)
    ) * 100

    score = max(0.0, min(score, 100.0))

    return DriftResult(
        composite_score=score,
        verbosity_delta=avg_verb,
        structural_distance=avg_struct,
        complexity_gini_delta=avg_comp,
        naming_violation_rate=avg_naming,
        per_file_scores=per_file,
        severity=_severity(score),
    )
