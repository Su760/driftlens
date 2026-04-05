"""Baseline system: create, save, and load metric snapshots for drift comparison."""

import json
from dataclasses import asdict
from pathlib import Path

from driftlens.metrics.complexity import compute_complexity_profile
from driftlens.metrics.naming import NamingProfile, analyze_naming
from driftlens.metrics.structure import compute_fingerprint
from driftlens.metrics.verbosity import compute_verbosity


def _serialize_fingerprint(fp: dict[tuple[str, int], int]) -> dict[str, int]:
    """Convert (NodeType, depth) tuple keys to 'NodeType:depth' strings."""
    return {f"{node_type}:{depth}": count for (node_type, depth), count in fp.items()}


def _deserialize_fingerprint(data: dict[str, int]) -> dict[tuple[str, int], int]:
    """Convert 'NodeType:depth' strings back to (NodeType, depth) tuple keys."""
    result: dict[tuple[str, int], int] = {}
    for key, count in data.items():
        node_type, depth_str = key.rsplit(":", 1)
        result[(node_type, int(depth_str))] = count
    return result


def create_baseline(project_dir: str) -> dict:
    """Scan all .py files and compute all 4 metrics for each.

    Returns a dict keyed by relative file path with metric values.
    """
    base = Path(project_dir)
    baseline: dict = {}

    for filepath in sorted(base.rglob("*.py")):
        rel = str(filepath.relative_to(base))
        fp_str = str(filepath)

        baseline[rel] = {
            "verbosity_ratio": compute_verbosity(fp_str),
            "structural_fingerprint": compute_fingerprint(fp_str),
            "complexity_gini": compute_complexity_profile(fp_str).gini,
            "naming_profile": asdict(analyze_naming(fp_str)),
        }

    return baseline


def save_baseline(baseline: dict, output_path: str) -> None:
    """Serialize baseline to JSON, converting tuple keys for JSON compatibility."""
    serializable = {}
    for rel, metrics in baseline.items():
        serializable[rel] = {
            "verbosity_ratio": metrics["verbosity_ratio"],
            "structural_fingerprint": _serialize_fingerprint(
                metrics["structural_fingerprint"]
            ),
            "complexity_gini": metrics["complexity_gini"],
            "naming_profile": metrics["naming_profile"],
        }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(serializable, indent=2))


def load_baseline(baseline_path: str) -> dict:
    """Load baseline from JSON, reconstructing tuple keys and dataclasses."""
    data = json.loads(Path(baseline_path).read_text())

    baseline: dict = {}
    for rel, metrics in data.items():
        baseline[rel] = {
            "verbosity_ratio": metrics["verbosity_ratio"],
            "structural_fingerprint": _deserialize_fingerprint(
                metrics["structural_fingerprint"]
            ),
            "complexity_gini": metrics["complexity_gini"],
            "naming_profile": NamingProfile(**metrics["naming_profile"]),
        }

    return baseline
