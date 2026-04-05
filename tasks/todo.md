# DriftLens — Task Log

## Day 1 (2026-04-05)

- [x] Scaffold project structure (pyproject.toml, src layout, tests/)
- [x] Implement verbosity metric (AST-based, per-function + file-level average)
- [x] Create test fixtures (clean.py ~28 lines, bloated.py ~130 lines)
- [x] Write tests (8 tests covering main path + edge cases)
- [ ] Verify tests pass
- [ ] Git init + initial commit

## Upcoming (Day 2+)

- [ ] CLI: `driftlens scan <path>` with Rich table output
- [ ] Structural metric: nesting depth + class cohesion
- [ ] Complexity metric: cyclomatic via radon
- [ ] Naming metric: identifier entropy / length distribution
- [ ] Baseline: save/load JSON snapshots
- [ ] Scorer: composite 0-100 drift score
- [ ] Storage: persist snapshots
- [ ] FastAPI CI endpoint
- [ ] GitHub Action integration
