# DriftLens

**AI coding agents make you faster. DriftLens makes sure they don't make your code worse.**

[![PyPI version](https://img.shields.io/pypi/v/driftlens.svg)](https://pypi.org/project/driftlens/)
[![Python versions](https://img.shields.io/pypi/pyversions/driftlens.svg)](https://pypi.org/project/driftlens/)
[![Tests](https://github.com/Su760/driftlens/actions/workflows/test.yml/badge.svg)](https://github.com/Su760/driftlens/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI agents write code at superhuman speed — but [SlopCodeBench (arXiv:2603.24755)](https://arxiv.org/abs/2603.24755) shows they produce **2.2x more verbose code** than humans, and code quality **degrades in 80% of agentic trajectories**. DriftLens catches this drift before it ships: baseline your codebase, then score every change against it.

---

## Quick start (30 seconds)

```bash
pip install driftlens
cd your-project
driftlens init        # snapshot current state as baseline
driftlens report      # score drift since baseline
```

---

## What it measures

DriftLens tracks four structural signals, all computed from the AST — no regex, no LLM calls.

| Metric                       | What it captures                                                                                                                    |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Verbosity ratio**          | Lines per logical operation — AI agents pad code with redundant assignments, dead branches, and over-commented obvious logic        |
| **Structural similarity**    | Cosine distance between AST fingerprints — catches wholesale rewrites that preserve behavior but destroy architecture               |
| **Complexity concentration** | Gini coefficient over cyclomatic complexity — flags when complexity pools into a few giant functions instead of staying distributed |
| **Naming consistency**       | Identifier entropy and length distribution — detects drift toward generic names (`data`, `result`, `tmp`) or absurdly verbose ones  |

These four signals are combined into a single **composite drift score (0–100)**. Higher = more drift from your baseline.

---

## CLI commands

| Command            | Description                                               |
| ------------------ | --------------------------------------------------------- |
| `driftlens init`   | Snapshot the current codebase as the baseline             |
| `driftlens score`  | Print the composite drift score (0–100)                   |
| `driftlens report` | Full breakdown — per-metric scores with Rich table output |
| `driftlens ci`     | Exit 1 if drift score exceeds threshold (for CI gates)    |

---

## CI/CD integration

Drop this into any GitHub Actions workflow to gate PRs on drift:

```yaml
- uses: Su760/driftlens@main
  with:
    threshold: "40"
```

DriftLens will fail the job if the composite drift score exceeds the threshold, printing a breakdown so you know exactly which metric regressed.

Full workflow example:

```yaml
name: Drift check
on: [pull_request]

jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: Su760/driftlens@main
        with:
          threshold: "40"
```

---

## Severity levels

| Score  | Severity    | Meaning                                       |
| ------ | ----------- | --------------------------------------------- |
| 0–15   | Healthy     | Code is consistent with baseline              |
| 16–35  | Mild        | Minor drift; worth a second look              |
| 36–60  | Significant | Structural changes detected; review carefully |
| 61–100 | Critical    | Major drift; likely AI-introduced degradation |

---

## How it works

**Step 1 — Baseline.** `driftlens init` walks your source tree, computes the four metrics for every Python file, and saves a JSON snapshot in `.driftlens/baseline.json`. This snapshot is your ground truth.

**Step 2 — Drift detection.** On every subsequent run, DriftLens recomputes the same metrics and compares them against the snapshot. Each metric returns a normalized delta (0–1), where 0 means identical and 1 means maximum measurable deviation.

**Step 3 — Scoring.** The four deltas are combined into a composite score using fixed weights:

```
score = 0.30 × verbosity + 0.30 × structure + 0.25 × complexity + 0.15 × naming
```

The result is scaled to 0–100. Verbosity and structure carry the most weight because they are the primary failure modes documented in SlopCodeBench.

All metrics are AST-based. DriftLens never calls an LLM, never sends your code anywhere, and produces deterministic results. A CI run that passes locally will pass remotely.

---

## Contributing

Pull requests are welcome. Before opening one:

1. Run `pytest tests/ -v` — all tests must pass
2. Do not modify files in `tests/fixtures/` — they are calibrated ground truth
3. New metrics follow the same pattern: `analyze_*` → `compute_*` → `compare_*`

See [CONTRIBUTING.md](CONTRIBUTING.md) for more detail.

---

## License

MIT — see [LICENSE](LICENSE).
