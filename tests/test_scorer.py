import shutil

import pytest

from driftlens.scorer import DriftResult, _severity, compute_drift

CLEAN = "tests/fixtures/clean.py"
BLOATED = "tests/fixtures/bloated.py"


def test_severity_healthy():
    assert _severity(0) == "healthy"
    assert _severity(10) == "healthy"
    assert _severity(15) == "healthy"


def test_severity_mild():
    assert _severity(16) == "mild"
    assert _severity(25) == "mild"
    assert _severity(35) == "mild"


def test_severity_significant():
    assert _severity(36) == "significant"
    assert _severity(40) == "significant"
    assert _severity(60) == "significant"


def test_severity_critical():
    assert _severity(61) == "critical"
    assert _severity(70) == "critical"
    assert _severity(100) == "critical"


def test_identical_dirs_zero_drift(tmp_path):
    # Copy clean.py into two identical directories
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    shutil.copy(CLEAN, dir_a / "code.py")
    shutil.copy(CLEAN, dir_b / "code.py")

    result = compute_drift(str(dir_a), str(dir_b))
    assert isinstance(result, DriftResult)
    assert result.composite_score == pytest.approx(0.0, abs=1e-9)
    assert result.severity == "healthy"


def test_clean_vs_bloated_positive_drift(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    shutil.copy(CLEAN, dir_a / "code.py")
    shutil.copy(BLOATED, dir_b / "code.py")

    result = compute_drift(str(dir_a), str(dir_b))
    assert result.composite_score > 0.0
    assert len(result.per_file_scores) == 1


def test_new_file_gets_max_structural_drift(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    # baseline is empty, current has a file → new file
    shutil.copy(CLEAN, dir_b / "new.py")

    result = compute_drift(str(dir_a), str(dir_b))
    assert result.structural_distance == 1.0


def test_empty_dirs_zero_drift(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    result = compute_drift(str(dir_a), str(dir_b))
    assert result.composite_score == 0.0
    assert result.severity == "healthy"


def test_deleted_file_skipped(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    # baseline has file, current does not → deleted, should be skipped
    shutil.copy(CLEAN, dir_a / "old.py")

    result = compute_drift(str(dir_a), str(dir_b))
    assert result.composite_score == 0.0
    assert len(result.per_file_scores) == 0
