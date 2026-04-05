# DriftLens

Code quality drift monitor for AI-generated code.

## Stack

- Python 3.11+, Click CLI, radon, rich
- AST-based metrics (no regex)
- pytest for tests

## Architecture

```
src/driftlens/
├── cli.py                  Click entry point
├── baseline.py             Save/load baseline snapshots
├── scorer.py               Composite drift score (0-100)
├── storage.py              Persist snapshots
└── metrics/
    ├── verbosity.py        Lines per logical operation
    ├── structure.py        AST fingerprint cosine distance
    ├── complexity.py       Gini coefficient over cyclomatic CC
    └── naming.py           Identifier entropy / length distribution
```

Each metric follows the same pattern:

- `analyze_*(filepath)` → list of per-function dataclasses
- `compute_*(filepath)` → single float summary
- `compare_*(baseline, current)` → delta

## Composite Drift Score

```
score = 0.30 * verbosity + 0.30 * structure + 0.25 * complexity + 0.15 * naming
```

Final score is normalized to 0–100. Higher = more drift from baseline.

## Tests

```bash
pytest tests/ -v
```

Fixtures live in `tests/fixtures/` — `clean.py` and `bloated.py` are calibrated baselines.

**Do NOT modify files in `tests/fixtures/` without asking.** They are the ground truth for metric calibration.

## Current State

| Metric     | Status    |
| ---------- | --------- |
| verbosity  | Complete  |
| structure  | Complete  |
| complexity | Complete  |
| naming     | Complete  |
| scorer     | Complete  |
| baseline   | Complete  |
| CLI        | Stub only |
