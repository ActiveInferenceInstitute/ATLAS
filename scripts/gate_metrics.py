#!/usr/bin/env python3
"""Measure the gate arms and generate `docs/_generated/GATE.md`.

The arm list and the exact commands come from `./gate --list`, so this script
never keeps a second copy of a command. Timings are wall-clock seconds from one
run of each arm on this host; they are environment facts, not a benchmark.

    ./gate measure                  # measure and rewrite the generated page
    python scripts/gate_metrics.py --check   # fail if the page drifted

`--check` compares only the reproducible part of the page (the set of arms)
against `./gate --list`. Timings are point-in-time samples, and the command
column shows the interpreter that was resolved on the measuring host, so
neither can be compared across hosts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import platform
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "_generated" / "GATE.md"
GATE = ROOT / "gate"
MEASURED = ("lint", "docs", "fast", "test")
OPTIONAL = ("gnn",)
SETUP_DEBT = ("src", "tests", "scripts")
SUMMARY = re.compile(r"(?:^|,\s*)(\d+) (passed|skipped|failed|error|errors|warnings)")


def gate_list() -> list[tuple[str, str]]:
    out = subprocess.run(
        [str(GATE), "--list"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    arms = []
    for line in out.splitlines():
        if not line.strip():
            continue
        arm, _, command = line.partition("\t")
        arms.append((arm, command))
    return arms


def version_of(module: str) -> str:
    try:
        import importlib.metadata as md

        return md.version(module)
    except Exception:  # pragma: no cover - environment dependent
        return "unavailable"


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_arm(arm: str) -> dict:
    start = time.monotonic()
    proc = subprocess.run(
        [str(GATE), arm], cwd=ROOT, capture_output=True, text=True
    )
    wall = time.monotonic() - start
    tail = [line for line in proc.stdout.splitlines() if line.strip()]
    result = "ok" if proc.returncode == 0 else f"FAILED (exit {proc.returncode})"
    return {
        "arm": arm,
        "wall": wall,
        "result": result,
        "output": "\n".join(tail[-40:]),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def pytest_counts(text: str) -> dict[str, int]:
    """Read the last pytest summary line; the gate appends its own footer."""
    counts: dict[str, int] = {}
    for line in reversed(text.strip().splitlines()):
        found = SUMMARY.findall(line)
        if not any(kind in {"passed", "failed", "error", "errors"} for _, kind in found):
            continue
        for count, kind in found:
            key = "error" if kind == "errors" else kind
            counts[key] = int(count)
        break
    return counts


def style_debt() -> str:
    python = sys.executable
    try:
        proc = subprocess.run(
            [python, "-m", "flake8", "--isolated", "--select=E,W,F", *SETUP_DEBT],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except OSError:  # pragma: no cover - environment dependent
        return "unavailable (flake8 not installed)"
    if proc.returncode not in (0, 1):
        return f"unavailable (flake8 exit {proc.returncode})"
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return "0 findings"
    codes: dict[str, int] = {}
    for line in lines:
        match = re.search(r"\b([EWF]\d{3})\b", line)
        if match:
            codes[match.group(1)] = codes.get(match.group(1), 0) + 1
    top = ", ".join(
        f"{code}: {count}"
        for code, count in sorted(codes.items(), key=lambda kv: -kv[1])[:6]
    )
    return f"{len(lines)} findings (top codes — {top})"


def interpreter_label() -> str:
    """Repository-relative interpreter path; never a machine-specific absolute path."""
    try:
        return f"./{pathlib.Path(sys.executable).relative_to(ROOT)}"
    except ValueError:
        return f"external interpreter ({platform.python_version()})"


def environment() -> list[tuple[str, str]]:
    return [
        ("Measured at (UTC)", dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")),
        ("Commit", f"`{git_commit()}`"),
        ("Host", f"{platform.system()} {platform.release()} ({platform.machine()})"),
        ("Python", f"{platform.python_version()} (`{interpreter_label()}`)"),
        ("pytest", version_of("pytest")),
        ("flake8", version_of("flake8")),
    ]


def render(rows: dict[str, dict | None], arms: list[tuple[str, str]]) -> str:
    env = environment()
    lines = [
        "# Gate arm timings",
        "",
        "<!-- generated by scripts/gate_metrics.py; refresh with ./gate measure -->",
        "",
        "Wall-clock seconds for one run of each arm on the host below. The arms and",
        "their commands come from `./gate --list`; this page is the only place the",
        "measured numbers live, and it is rewritten by `./gate measure` rather than",
        "edited by hand. `./gate docs` fails when the arm table here drifts from the",
        "gate.",
        "",
        "## Environment",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    lines += [f"| {key} | {value} |" for key, value in env]
    lines += [
        "",
        "## Arms",
        "",
        "| Arm | Wall time (s) | Result | Command (as resolved on the measuring host) |",
        "| --- | --- | --- | --- |",
    ]
    for arm, command in arms:
        row = rows.get(arm)
        if row is None:
            wall, result = "not measured", "run outside this page"
        else:
            wall, result = f"{row['wall']:.2f}", row["result"]
        lines.append(f"| `{arm}` | {wall} | {result} | `{command}` |")
    lines += [
        "",
        "`setup` is an install step rather than a check, so its duration depends on",
        "the local wheel cache and is not recorded here. `gnn` needs network access to",
        "install the pinned parser and fetch the pinned exemplar; CI runs it in its own",
        "job, and `./gate measure --include-gnn` records it when a network is available.",
        "",
        "## Test counts",
        "",
        "| Arm | Reported by pytest |",
        "| --- | --- |",
    ]
    for arm in ("fast", "test"):
        row = rows.get(arm)
        if row is None:
            lines.append(f"| `{arm}` | not measured |")
            continue
        counts = pytest_counts(row["stdout"])
        rendered = ", ".join(f"{value} {key}" for key, value in sorted(counts.items()))
        lines.append(f"| `{arm}` | {rendered or 'no summary line'} |")
    lines += [
        "",
        "## Not gated",
        "",
        f"`./gate lint` selects only fatal-error codes (`.flake8`). Under flake8's full",
        f"default selection the tree currently reports: {style_debt()}.",
        "That debt is tracked in [TO-DO.md](../../TO-DO.md) and is not a gate failure.",
        "",
        "## Verification",
        "",
        "```bash",
        "./gate all      # lint, docs, fast, test",
        "./gate gnn      # pinned conformance; needs network",
        "./gate measure  # rewrite this page",
        "```",
        "",
    ]
    return "\n".join(lines)


def write_document(rows: dict[str, dict | None], arms: list[tuple[str, str]]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(rows, arms), encoding="utf-8")


def check(arms: list[tuple[str, str]]) -> int:
    if not OUT.is_file():
        print(f"{OUT.relative_to(ROOT)} is missing; run ./gate measure", file=sys.stderr)
        return 1
    text = OUT.read_text(encoding="utf-8")
    recorded: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\| `([a-z]+)` \| .* \| `(.+)` \|$", line)
        if match:
            recorded.add(match.group(1))
    expected = {arm for arm, _ in arms}
    problems = [
        f"{arm}: missing from {OUT.relative_to(ROOT)}" for arm in sorted(expected - recorded)
    ]
    problems += [f"{arm}: recorded but not a gate arm" for arm in sorted(recorded - expected)]
    if problems:
        print("gate metrics page is stale; run ./gate measure:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"gate metrics page lists exactly the ./gate arms ({len(expected)} arms).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the page is current")
    parser.add_argument(
        "--include-gnn", action="store_true", help="also measure the network-bound gnn arm"
    )
    args = parser.parse_args(argv)

    arms = gate_list()
    arm_names = [arm for arm, _ in arms]
    to_measure = [arm for arm in MEASURED if arm in arm_names]
    if args.include_gnn:
        to_measure += [arm for arm in OPTIONAL if arm in arm_names]

    if args.check:
        return check(arms)

    rows: dict[str, dict | None] = {
        arm: None for arm, _ in arms if arm in to_measure
    }
    # Write the arm table first so the docs arm's own freshness check passes.
    write_document(rows, arms)

    failed = False
    for arm in to_measure:
        row = run_arm(arm)
        rows[arm] = row
        print(
            json.dumps(
                {"arm": arm, "wall": round(row["wall"], 2), "result": row["result"]},
                sort_keys=True,
            )
        )
        failed |= row["result"] != "ok"
    write_document(rows, arms)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
