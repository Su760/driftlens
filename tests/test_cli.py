"""CLI integration tests using Click's CliRunner."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from driftlens.cli import cli

CLEAN_FIXTURE = Path("tests/fixtures/clean.py")
BLOATED_FIXTURE = Path("tests/fixtures/bloated.py")


@pytest.fixture
def project(tmp_path):
    """A minimal project directory with a copy of clean.py."""
    src = tmp_path / "mymod"
    src.mkdir()
    shutil.copy(CLEAN_FIXTURE, src / "main.py")
    return tmp_path


@pytest.fixture
def initialized_project(project):
    """project with baseline already saved."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(project)])
    assert result.exit_code == 0, result.output
    return project


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_init_creates_baseline_json(project):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(project)])

    assert result.exit_code == 0, result.output
    baseline_path = project / ".driftlens" / "baseline.json"
    assert baseline_path.exists()

    data = json.loads(baseline_path.read_text())
    assert len(data) > 0
    first_entry = next(iter(data.values()))
    assert "verbosity_ratio" in first_entry
    assert "structural_fingerprint" in first_entry
    assert "complexity_gini" in first_entry
    assert "naming_profile" in first_entry


def test_init_reports_file_count(project):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(project)])
    assert "Files scanned" in result.output
    assert "1" in result.output  # one .py file in the project


def test_init_missing_directory():
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", "/nonexistent/path/xyz"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# score — identical file → exit 0
# ---------------------------------------------------------------------------


def test_score_identical_file_exits_zero(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["score", "--path", str(initialized_project)])
    # Exit 0 because drift should be near 0 (same file)
    assert result.exit_code == 0, result.output


def test_score_produces_table_output(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["score", "--path", str(initialized_project)])
    assert "Drift" in result.output or "drift" in result.output.lower()
    assert "main.py" in result.output


def test_score_no_baseline_exits_nonzero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["score", "--path", str(tmp_path)])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# score — bloated file → exit 1 when score exceeds threshold
# ---------------------------------------------------------------------------


def test_score_bloated_exceeds_threshold(tmp_path):
    """Replace clean.py with bloated.py after init — score should exceed low threshold."""
    src = tmp_path / "mymod"
    src.mkdir()
    shutil.copy(CLEAN_FIXTURE, src / "main.py")

    runner = CliRunner()
    init_result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
    assert init_result.exit_code == 0, init_result.output

    # Swap in the bloated file
    shutil.copy(BLOATED_FIXTURE, src / "main.py")

    # Use a very low threshold — bloated vs clean should exceed 5
    result = runner.invoke(cli, ["score", "--path", str(tmp_path), "--threshold", "5"])
    assert result.exit_code == 1, (
        f"Expected exit 1 (drift > 5) but got {result.exit_code}.\nOutput:\n{result.output}"
    )


def test_score_specific_files_flag(initialized_project):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["score", "--path", str(initialized_project), "--files", "mymod/main.py"],
    )
    assert result.exit_code == 0, result.output
    assert "main.py" in result.output


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def test_report_runs_without_error(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--path", str(initialized_project)])
    assert result.exit_code == 0, result.output


def test_report_shows_overall_score(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--path", str(initialized_project)])
    assert "Overall Drift Score" in result.output or "drift" in result.output.lower()


def test_report_shows_top_files(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--path", str(initialized_project)])
    assert "main.py" in result.output


def test_report_no_baseline_exits_nonzero(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--path", str(tmp_path)])
    assert result.exit_code == 1
