#!/usr/bin/env python3
"""Lightweight documentation QA gate for the ATLAS repository.

Checks, using only the standard library (plus the system Ruby Psych YAML
parser, preinstalled on macOS and on GitHub-hosted Ubuntu runners):

1. No trailing whitespace in tracked markdown, YAML, and CFF files.
2. Every relative link in markdown files resolves to an existing path, and
   every in-file anchor fragment resolves to a heading.
3. .aii/config.yaml and CITATION.cff parse as YAML.

Exit code is non-zero on any failure, so the script can be used as a CI gate
(.github/workflows/docs-qa.yml) and as a local pre-commit check. See
AGENTS.md for repository conventions.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUFFIXES = (".md", ".yaml", ".yml", ".cff")


def tracked_files() -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [ROOT / p for p in out.stdout.splitlines() if p]


def check_trailing_whitespace(files: list[pathlib.Path], errors: list[str]) -> None:
    for f in files:
        if f.suffix not in SUFFIXES:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f"{f.relative_to(ROOT)}:{i}: trailing whitespace")


def check_links(files: list[pathlib.Path], errors: list[str]) -> None:
    for f in files:
        if f.suffix != ".md":
            continue
        text = f.read_text(encoding="utf-8")
        headings = {
            re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-")
            for h in re.findall(r"^#{1,6}\s+(.*)$", text, re.M)
        }
        for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            path_part, _, frag = target.partition("#")
            if not path_part:
                if frag and frag not in headings:
                    errors.append(f"{f.relative_to(ROOT)}: broken anchor #{frag}")
                continue
            if not (f.parent / path_part).resolve().exists():
                errors.append(f"{f.relative_to(ROOT)}: broken link {target!r}")


def check_yaml(files: list[pathlib.Path], errors: list[str]) -> None:
    for name in (".aii/config.yaml", "CITATION.cff"):
        target = ROOT / name
        if target not in files:
            errors.append(f"{name}: not tracked")
            continue
        ruby = subprocess.run(
            ["ruby", "-ryaml", "-e", "YAML.load_file(ARGV[0])", str(target)],
            capture_output=True,
            text=True,
        )
        if ruby.returncode != 0:
            errors.append(f"{name}: YAML parse failed: {ruby.stderr.strip()}")


def main() -> int:
    files = tracked_files()
    errors: list[str] = []
    check_trailing_whitespace(files, errors)
    check_links(files, errors)
    check_yaml(files, errors)
    if errors:
        print(f"docs QA failed ({len(errors)} issue(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("docs QA passed: whitespace, links/anchors, and YAML all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
