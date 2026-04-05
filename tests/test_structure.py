import os
import tempfile

from driftlens.metrics.structure import (
    compare_structure,
    compute_fingerprint,
    compute_structural_distance,
)

CLEAN = "tests/fixtures/clean.py"
BLOATED = "tests/fixtures/bloated.py"


def test_fingerprint_has_expected_keys():
    fp = compute_fingerprint(CLEAN)
    node_types = {node_type for node_type, _ in fp}
    assert "FunctionDef" in node_types
    assert "Module" in node_types
    assert "Return" in node_types


def test_identical_files_distance_zero():
    fp = compute_fingerprint(CLEAN)
    assert compute_structural_distance(fp, fp) == 0.0


def test_same_file_compared_twice_distance_zero():
    fp_a = compute_fingerprint(CLEAN)
    fp_b = compute_fingerprint(CLEAN)
    assert compute_structural_distance(fp_a, fp_b) == 0.0


def test_clean_vs_bloated_distance_gt_zero():
    fp_clean = compute_fingerprint(CLEAN)
    fp_bloated = compute_fingerprint(BLOATED)
    dist = compute_structural_distance(fp_clean, fp_bloated)
    assert dist > 0.0, f"Expected structural distance > 0, got {dist}"


def test_distance_range():
    fp_clean = compute_fingerprint(CLEAN)
    fp_bloated = compute_fingerprint(BLOATED)
    dist = compute_structural_distance(fp_clean, fp_bloated)
    assert 0.0 <= dist <= 1.0


def test_empty_file_returns_empty_fingerprint():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        tmpfile = f.name
    try:
        fp = compute_fingerprint(tmpfile)
        assert fp == {}
    finally:
        os.unlink(tmpfile)


def test_empty_vs_empty_distance_zero():
    assert compute_structural_distance({}, {}) == 0.0


def test_empty_vs_nonempty_distance_one():
    fp = compute_fingerprint(CLEAN)
    assert compute_structural_distance({}, fp) == 1.0
    assert compute_structural_distance(fp, {}) == 1.0


def test_compare_structure_delegates_to_distance():
    fp_a = compute_fingerprint(CLEAN)
    fp_b = compute_fingerprint(BLOATED)
    assert compare_structure(fp_a, fp_b) == compute_structural_distance(fp_a, fp_b)
