# The gate

`./gate` is the single entry point for every check in this repository. Each
check is an arm, arms are runnable on their own, and CI runs these exact arms —
the workflow holds no command of its own. `./gate --list` prints every arm with
the exact command it runs; this page describes what each one covers.

## Arms

| Arm | Covers | Needs network |
| --- | --- | --- |
| `setup` | Installs the one environment the other arms share (`-e .[dev,viz,obsidian]`). | yes, first run |
| `lint` | `flake8` over `src`, `tests`, `scripts`, using the committed `.flake8`. | no |
| `docs` | `scripts/docs_qa.py` (whitespace, links, same-file/cross-file heading anchors, YAML, Publishing artifact digests) and the generated-page check. | no |
| `fast` | The test suite without the `slow` marker. | no |
| `test` | The full test suite. | no |
| `gnn` | Pinned GNN conformance against `.github/gnn-pin.json`. | yes |
| `all` | `lint`, `docs`, `test` — the offline-safe set. | no |
| `measure` | Re-measures the arms into [`_generated/GATE.md`](_generated/GATE.md). | no |

With no argument the gate runs `fast`: the quick developer loop.

The [Publishing member contract](workflows/publishing.md) pins the canonical
identity schema, checker, and GNN pin. The docs arm runs the copied lead checker
offline, including `--verify-copy` for each pinned artifact; it does not scan a
journal corpus or introduce another gate entry point.

## Environment

The gate resolves one interpreter — `$PYTHON` if set, else `.venv/bin/python`
when it exists, else `python3` — and every arm uses it. `./gate setup` is the
only install step; the `lint` and `test` arms both use what it leaves behind, so
CI installs once per job instead of once per arm.

## Selection

`tests/test_atlas_performance.py` carries the `slow` marker (registered in
`pyproject.toml`), so `fast` is `pytest -m "not slow"` and `test` is plain
`pytest`. Both arms report their own counts; the measured numbers live in
[`_generated/GATE.md`](_generated/GATE.md), never in prose.

## No types arm

`pyproject.toml` declares `mypy` in the `dev` extra, but nothing in the
repository runs it, configures it, or annotates the package for it. Gating type
checking would report on a surface the code has not been prepared for, so there
is no types arm; adding one is a separate, evidence-backed change.

## Lint scope

`.flake8` selects only the fatal-error codes (`E9`, `F63`, `F7`, `F82`). The
tree still carries pre-existing style debt under flake8's full default
selection; the current count and its top codes are recorded in
[`_generated/GATE.md`](_generated/GATE.md) and tracked in
[`../TO-DO.md`](../TO-DO.md). The lint arm gates what the code is clean on and
does not hide the rest.

## CI

`.github/workflows/gate.yml` is the only workflow:

| Job key | Display name | Runs |
| --- | --- | --- |
| `gate` | `gate (python 3.11)` / `gate (python 3.14)` | `./gate setup`, `./gate lint`, `./gate test` — one checkout, one install |
| `docs` | `docs` | `./gate docs` on the runner's Python; no install step |
| `gnn-conformance` | `gnn conformance (pinned)` | `./gate gnn` on Python 3.12 |

Actions are pinned to `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1) and `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`
(v7.1.0). This repository does not use the shared
`ActiveInferenceInstitute/.github` `setup-python-uv` composite action: it
installs with `pip` from `pyproject.toml` and has no `uv` lock file.

## GNN conformance

`.github/GNN.md` records what the `gnn` arm parses. It reads the canonical pin
[`../.github/gnn-pin.json`](../.github/gnn-pin.json) (schema
`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`). The arm installs the pinned
parser with `--no-deps` plus the runtime modules it imports, and verifies what
is installed against the pin: the version must match `tag`, and PEP 610
`direct_url.json` must name the pinned repository and commit. An existing
install is reused only when that provenance matches; otherwise the pinned spec
is force-reinstalled — a version string is not proof of which commit produced
it. The arm then parses and type-checks every `*.gnn.md`
sketch in the repository — or, as ATLAS currently has none, the pinned upstream
`input/gnn_files/basics/static_perception.md` exemplar.

Because the parser install and the exemplar fetch need network access, `gnn`
is not part of `all`. `./gate measure --include-gnn` records it when a network
is available. `scripts/gnn_conformance.py --no-install` requires the same
provenance from an existing install and fails rather than accepting a parser
that only reports the pinned version.

## Refreshing the measured page

```bash
./gate measure
```

[`_generated/GATE.md`](_generated/GATE.md) is generated: it names the host,
interpreter, and commit it was measured on, lists every arm with its wall time,
and records the pytest counts. The docs arm fails when its arm table drifts from
`./gate --list`, so an added or renamed arm cannot leave a stale page behind.
