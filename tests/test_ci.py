"""Tests for the `driftlens ci` command."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from driftlens.cli import cli

CLEAN_FIXTURE = Path("tests/fixtures/clean.py")
BLOATED_FIXTURE = Path("tests/fixtures/bloated.py")


@pytest.fixture
def initialized_project(tmp_path):
    """Project with a clean baseline already saved."""
    src = tmp_path / "mymod"
    src.mkdir()
    shutil.copy(CLEAN_FIXTURE, src / "main.py")

    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    return tmp_path


def test_ci_exits_zero_for_identical_baseline(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["ci", "--path", str(initialized_project)])
    assert result.exit_code == 0, result.output


def test_ci_exits_one_when_threshold_exceeded(tmp_path):
    src = tmp_path / "mymod"
    src.mkdir()
    shutil.copy(CLEAN_FIXTURE, src / "main.py")

    runner = CliRunner()
    init_result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
    assert init_result.exit_code == 0, init_result.output

    # Swap in bloated file — drift should exceed threshold of 5
    shutil.copy(BLOATED_FIXTURE, src / "main.py")

    result = runner.invoke(cli, ["ci", "--path", str(tmp_path), "--threshold", "5"])
    assert result.exit_code == 1, (
        f"Expected exit 1 (drift > 5) but got {result.exit_code}.\nOutput:\n{result.output}"
    )


def test_ci_json_output_is_valid_with_expected_keys(initialized_project):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["ci", "--path", str(initialized_project), "--format", "json"]
    )
    assert result.exit_code == 0, result.output

    data = json.loads(result.output)
    assert "overall_score" in data
    assert "threshold" in data
    assert "passed" in data
    assert "severity" in data
    assert "files" in data
    assert isinstance(data["files"], list)
    assert len(data["files"]) > 0

    first_file = data["files"][0]
    assert "filepath" in first_file
    assert "composite_score" in first_file


def test_ci_text_output_contains_score(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["ci", "--path", str(initialized_project)])
    assert result.exit_code == 0, result.output
    assert "overall:" in result.output
    assert "threshold:" in result.output
    assert "PASS" in result.output
