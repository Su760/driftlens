import shutil

from driftlens.baseline import create_baseline, load_baseline, save_baseline
from driftlens.metrics.naming import NamingProfile

CLEAN = "tests/fixtures/clean.py"


def test_create_baseline_has_expected_keys(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    shutil.copy(CLEAN, proj / "main.py")

    baseline = create_baseline(str(proj))
    assert "main.py" in baseline

    entry = baseline["main.py"]
    assert "verbosity_ratio" in entry
    assert "structural_fingerprint" in entry
    assert "complexity_gini" in entry
    assert "naming_profile" in entry


def test_save_load_roundtrip(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    shutil.copy(CLEAN, proj / "main.py")

    baseline = create_baseline(str(proj))
    out = tmp_path / "baseline.json"
    save_baseline(baseline, str(out))

    loaded = load_baseline(str(out))
    assert "main.py" in loaded

    entry = loaded["main.py"]
    assert entry["verbosity_ratio"] == baseline["main.py"]["verbosity_ratio"]
    assert entry["complexity_gini"] == baseline["main.py"]["complexity_gini"]
    assert isinstance(entry["naming_profile"], NamingProfile)


def test_fingerprint_serialization_roundtrip(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    shutil.copy(CLEAN, proj / "main.py")

    baseline = create_baseline(str(proj))
    out = tmp_path / "baseline.json"
    save_baseline(baseline, str(out))
    loaded = load_baseline(str(out))

    orig_fp = baseline["main.py"]["structural_fingerprint"]
    loaded_fp = loaded["main.py"]["structural_fingerprint"]

    # Tuple keys must survive the JSON roundtrip
    assert isinstance(list(loaded_fp.keys())[0], tuple)
    assert orig_fp == loaded_fp
