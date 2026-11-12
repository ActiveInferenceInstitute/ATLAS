"""Regression coverage for documentation links and gate arm discovery."""

import importlib.util
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("docs_qa", ROOT / "scripts/docs_qa.py")
docs_qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(docs_qa)


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("#source-heading", []),
        ("#missing-heading", ["docs/source.md: broken anchor #missing-heading"]),
        ("other.md#target-heading", []),
        ("../target.md#target-heading", []),
        ("other.md#missing-heading", [
            "docs/source.md: broken anchor 'other.md#missing-heading'"
        ]),
        ("other.md#source-heading", [
            "docs/source.md: broken anchor 'other.md#source-heading'"
        ]),
        ("missing.md#target-heading", [
            "docs/source.md: broken link 'missing.md#target-heading'"
        ]),
        ("other.md", []),
        ("https://example.org/other.md#missing-heading", []),
    ],
)
def test_heading_fragments(tmp_path, monkeypatch, target, expected):
    monkeypatch.setattr(docs_qa, "ROOT", tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    source = docs / "source.md"
    source.write_text(f"# Source Heading\n\n[link]({target})\n", encoding="utf-8")
    (docs / "other.md").write_text("# Target Heading\n", encoding="utf-8")
    (tmp_path / "target.md").write_text("# Target Heading\n", encoding="utf-8")

    errors = []
    docs_qa.check_links([source], errors)

    assert errors == expected


def test_gate_lists_every_supported_arm():
    result = subprocess.run(
        [str(ROOT / "gate"), "--list"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    arms = dict(line.split("\t", 1) for line in result.stdout.splitlines())

    assert set(arms) == {"setup", "lint", "docs", "fast", "test", "gnn", "all", "measure"}
    assert arms["all"] == " && ".join(arms[arm] for arm in ("lint", "docs", "test"))
    assert arms["measure"].endswith(" scripts/gate_metrics.py")
