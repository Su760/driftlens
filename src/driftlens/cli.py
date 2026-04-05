import json
import sys
from collections import defaultdict
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from driftlens.baseline import create_baseline, load_baseline, save_baseline
from driftlens.metrics.complexity import compare_complexity, compute_complexity_profile
from driftlens.metrics.naming import analyze_naming, compare_naming
from driftlens.metrics.structure import compare_structure, compute_fingerprint
from driftlens.metrics.verbosity import compute_verbosity

console = Console()

BASELINE_FILE = ".driftlens/baseline.json"


def _severity(score: float) -> str:
    if score <= 15:
        return "healthy"
    if score <= 35:
        return "mild"
    if score <= 60:
        return "significant"
    return "critical"


SEVERITY_COLORS = {
    "healthy": "green",
    "mild": "yellow",
    "significant": "orange3",
    "critical": "red",
}


def _score_file(baseline_entry: dict, current_filepath: str) -> dict:
    """Compute per-metric deltas and composite score for one file against its baseline."""
    base_verb = baseline_entry["verbosity_ratio"]
    curr_verb = compute_verbosity(current_filepath)
    verb_delta = (curr_verb - base_verb) / base_verb if base_verb else 0.0

    base_fp = baseline_entry["structural_fingerprint"]
    curr_fp = compute_fingerprint(current_filepath)
    struct_dist = compare_structure(base_fp, curr_fp)

    base_gini = baseline_entry["complexity_gini"]
    curr_profile = compute_complexity_profile(current_filepath)
    comp_delta = compare_complexity(base_gini, curr_profile.gini)

    base_naming = baseline_entry["naming_profile"]
    curr_naming = analyze_naming(current_filepath)
    naming_vr = compare_naming(base_naming, curr_naming)

    composite = (
        0.30 * min(max(verb_delta, 0.0), 1.0)
        + 0.30 * min(max(struct_dist, 0.0), 1.0)
        + 0.25 * min(max(comp_delta * 2, 0.0), 1.0)
        + 0.15 * min(max(naming_vr, 0.0), 1.0)
    ) * 100

    return {
        "verbosity_delta": verb_delta,
        "structural_distance": struct_dist,
        "complexity_gini_delta": comp_delta,
        "naming_violation_rate": naming_vr,
        "composite_score": composite,
    }


def _score_color(score: float) -> str:
    return SEVERITY_COLORS[_severity(score)]


@click.group()
@click.version_option()
def cli() -> None:
    """DriftLens — code quality drift monitor for AI-generated code."""


@cli.command()
@click.option("--path", default=".", show_default=True, help="Project root to scan.")
def init(path: str) -> None:
    """Scan project and save a baseline snapshot."""
    project_dir = Path(path).resolve()
    if not project_dir.is_dir():
        console.print(f"[red]Error:[/red] {path!r} is not a directory.")
        sys.exit(1)

    console.print(f"[bold]Scanning[/bold] {project_dir} ...")

    baseline = create_baseline(str(project_dir))
    if not baseline:
        console.print("[yellow]No .py files found — baseline not saved.[/yellow]")
        sys.exit(0)

    output_path = project_dir / BASELINE_FILE
    save_baseline(baseline, str(output_path))

    file_count = len(baseline)
    console.print(
        f"[green]✓[/green] Baseline saved to [bold]{output_path}[/bold]\n"
        f"  Files scanned: [bold]{file_count}[/bold]"
    )


@cli.command()
@click.option("--path", default=".", show_default=True, help="Project root.")
@click.option(
    "--files",
    multiple=True,
    help="Specific files to score (relative to --path). Defaults to all .py files.",
)
@click.option(
    "--threshold",
    default=40,
    show_default=True,
    help="Exit code 1 if composite score exceeds this.",
)
def score(path: str, files: tuple, threshold: int) -> None:
    """Compute drift score against the saved baseline."""
    project_dir = Path(path).resolve()
    baseline_path = project_dir / BASELINE_FILE

    if not baseline_path.exists():
        console.print(
            f"[red]Error:[/red] No baseline found at {baseline_path}. "
            "Run [bold]driftlens init[/bold] first."
        )
        sys.exit(1)

    baseline = load_baseline(str(baseline_path))

    # Determine which files to score
    if files:
        target_files = [project_dir / f for f in files]
    else:
        target_files = sorted(project_dir.rglob("*.py"))

    results = []
    skipped = 0

    for filepath in target_files:
        rel = str(filepath.relative_to(project_dir))
        if rel not in baseline:
            skipped += 1
            continue
        result = _score_file(baseline[rel], str(filepath))
        result["filepath"] = rel
        results.append(result)

    if not results:
        console.print("[yellow]No files matched the baseline. Nothing to score.[/yellow]")
        sys.exit(0)

    composite_scores = [r["composite_score"] for r in results]
    overall = sum(composite_scores) / len(composite_scores)
    sev = _severity(overall)
    color = SEVERITY_COLORS[sev]

    # Per-file table
    table = Table(
        title="Per-file Drift Breakdown",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
    )
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Verbosity", justify="right")
    table.add_column("Structure", justify="right")
    table.add_column("Complexity", justify="right")
    table.add_column("Naming", justify="right")
    table.add_column("Composite", justify="right")

    for r in results:
        cscore = r["composite_score"]
        row_color = _score_color(cscore)
        table.add_row(
            r["filepath"],
            f"{r['verbosity_delta']:+.3f}",
            f"{r['structural_distance']:.3f}",
            f"{r['complexity_gini_delta']:+.3f}",
            f"{r['naming_violation_rate']:+.3f}",
            Text(f"{cscore:.1f}", style=f"bold {row_color}"),
        )

    console.print(table)

    if skipped:
        console.print(f"[dim]Skipped {skipped} file(s) not in baseline.[/dim]")

    score_text = Text(f"{overall:.1f} / 100", style=f"bold {color}")
    label = Text(f"  ({sev})", style=color)
    console.print("\nOverall drift score: ", end="")
    console.print(score_text, end="")
    console.print(label)

    if overall > threshold:
        console.print(
            f"[red]✗[/red] Score {overall:.1f} exceeds threshold {threshold} — exiting 1"
        )
        sys.exit(1)
    else:
        console.print(
            f"[green]✓[/green] Score {overall:.1f} is within threshold {threshold}"
        )


@cli.command()
@click.option("--path", default=".", show_default=True, help="Project root to scan.")
@click.option("--threshold", default=40, show_default=True, help="Exit code 1 if score exceeds this.")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), show_default=True, help="Output format.")
def ci(path: str, threshold: int, output_format: str) -> None:
    """CI-friendly drift check: plain text output, exits 1 if threshold exceeded."""
    project_dir = Path(path).resolve()
    baseline_path = project_dir / BASELINE_FILE

    if not baseline_path.exists():
        print(f"ERROR: No baseline found at {baseline_path}. Run 'driftlens init' first.")
        sys.exit(1)

    baseline = load_baseline(str(baseline_path))
    target_files = sorted(project_dir.rglob("*.py"))

    results = []
    for filepath in target_files:
        rel = str(filepath.relative_to(project_dir))
        if rel not in baseline:
            continue
        result = _score_file(baseline[rel], str(filepath))
        result["filepath"] = rel
        results.append(result)

    if not results:
        print("No files matched the baseline. Nothing to score.")
        sys.exit(0)

    overall = sum(r["composite_score"] for r in results) / len(results)
    passed = overall <= threshold

    if output_format == "json":
        output = {
            "overall_score": round(overall, 2),
            "threshold": threshold,
            "passed": passed,
            "severity": _severity(overall),
            "files": [
                {
                    "filepath": r["filepath"],
                    "composite_score": round(r["composite_score"], 2),
                    "verbosity_delta": round(r["verbosity_delta"], 4),
                    "structural_distance": round(r["structural_distance"], 4),
                    "complexity_gini_delta": round(r["complexity_gini_delta"], 4),
                    "naming_violation_rate": round(r["naming_violation_rate"], 4),
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            print(f"{r['filepath']}: {r['composite_score']:.1f}")
        print(f"overall: {overall:.1f} / 100  [{_severity(overall)}]")
        status = "PASS" if passed else "FAIL"
        print(f"threshold: {threshold}  result: {status}")

    # Post PR comment when running in GitHub Actions
    if _in_github_actions():
        try:
            from driftlens.github import post_pr_comment
            post_pr_comment(results, overall, threshold, passed)
        except Exception:
            pass  # Never let comment posting break the CI step

    sys.exit(0 if passed else 1)


def _in_github_actions() -> bool:
    import os
    return os.environ.get("GITHUB_ACTIONS") == "true"


@cli.command()
@click.option("--path", default=".", show_default=True, help="Project root.")
def report(path: str) -> None:
    """Rich terminal dashboard: overall drift, per-module breakdown, top drifting files."""
    project_dir = Path(path).resolve()
    baseline_path = project_dir / BASELINE_FILE

    if not baseline_path.exists():
        console.print(
            f"[red]Error:[/red] No baseline found at {baseline_path}. "
            "Run [bold]driftlens init[/bold] first."
        )
        sys.exit(1)

    baseline = load_baseline(str(baseline_path))

    results = []
    for rel, entry in baseline.items():
        filepath = project_dir / rel
        if not filepath.exists():
            continue
        result = _score_file(entry, str(filepath))
        result["filepath"] = rel
        results.append(result)

    if not results:
        console.print("[yellow]No files to score.[/yellow]")
        sys.exit(0)

    composite_scores = [r["composite_score"] for r in results]
    overall = sum(composite_scores) / len(composite_scores)
    sev = _severity(overall)
    color = SEVERITY_COLORS[sev]

    # --- Overall score panel ---
    score_text = Text(f"{overall:.1f} / 100", style=f"bold {color} on default", justify="center")
    console.print(
        Panel(
            score_text,
            title="[bold]Overall Drift Score[/bold]",
            subtitle=f"[{color}]{sev.upper()}[/{color}]",
            expand=False,
            padding=(0, 4),
        )
    )

    # --- Per-module breakdown ---
    modules: dict[str, list[float]] = defaultdict(list)
    for r in results:
        parts = Path(r["filepath"]).parts
        module = parts[0] if len(parts) > 1 else "(root)"
        modules[module].append(r["composite_score"])

    mod_table = Table(
        title="Per-module Breakdown",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    mod_table.add_column("Module", style="cyan")
    mod_table.add_column("Files", justify="right")
    mod_table.add_column("Avg Drift", justify="right")

    for mod, scores in sorted(modules.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        avg = sum(scores) / len(scores)
        mod_table.add_row(mod, str(len(scores)), Text(f"{avg:.1f}", style=_score_color(avg)))

    console.print(mod_table)

    # --- Top 5 worst drifting files ---
    top5 = sorted(results, key=lambda r: -r["composite_score"])[:5]
    top_table = Table(
        title="Top 5 Worst-drifting Files",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    top_table.add_column("File", style="cyan", no_wrap=True)
    top_table.add_column("Score", justify="right")
    top_table.add_column("Severity", justify="right")

    for r in top5:
        sc = r["composite_score"]
        sv = _severity(sc)
        top_table.add_row(r["filepath"], f"{sc:.1f}", Text(sv, style=SEVERITY_COLORS[sv]))

    console.print(top_table)

    # --- Metric-by-metric summary ---
    n = len(results)
    avg_verb = sum(r["verbosity_delta"] for r in results) / n
    avg_struct = sum(r["structural_distance"] for r in results) / n
    avg_comp = sum(r["complexity_gini_delta"] for r in results) / n
    avg_naming = sum(r["naming_violation_rate"] for r in results) / n

    # Weighted contribution (mirrors composite formula)
    contrib = {
        "verbosity": 0.30 * min(max(avg_verb, 0.0), 1.0) * 100,
        "structure": 0.30 * min(max(avg_struct, 0.0), 1.0) * 100,
        "complexity": 0.25 * min(max(avg_comp * 2, 0.0), 1.0) * 100,
        "naming": 0.15 * min(max(avg_naming, 0.0), 1.0) * 100,
    }
    top_contrib = max(contrib, key=contrib.get)  # type: ignore[arg-type]

    metric_table = Table(
        title="Metric Contributions",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    metric_table.add_column("Metric")
    metric_table.add_column("Avg Delta", justify="right")
    metric_table.add_column("Weighted pts", justify="right")

    metric_rows = [
        ("verbosity", f"{avg_verb:+.3f}", contrib["verbosity"]),
        ("structure", f"{avg_struct:.3f}", contrib["structure"]),
        ("complexity", f"{avg_comp:+.3f}", contrib["complexity"]),
        ("naming", f"{avg_naming:+.3f}", contrib["naming"]),
    ]
    for name, delta, pts in metric_rows:
        style = "bold yellow" if name == top_contrib else ""
        suffix = " ← highest" if name == top_contrib else ""
        metric_table.add_row(
            Text(name + suffix, style=style),
            Text(delta, style=style),
            Text(f"{pts:.1f}", style=style),
        )

    console.print(metric_table)
