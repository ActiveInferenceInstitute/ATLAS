# REVIEW LOG — 2026-11-01

Audit and alignment pass over the ATLAS repository
(ActiveInferenceInstitute/ATLAS): currency, packaging, optional-dependency
coverage, documentation accuracy, and the applied active inference framing.

## Phase 0 — Preflight

- Branch: `codex/gnn-alignment-20261101`, based on `main` =
  `1d521da` ("docs: finalize review log with CI status and QA portability
  fix"), working tree clean at the start.
- Remotes: `origin` = https://github.com/ActiveInferenceInstitute/ATLAS.git
  only (no external upstream tracking; the `docxology/ATLAS` reference fork is
  cited in the sidecar, not configured as a remote).
- Inventory: `src/atlas/` (26 modules, ~6,800 lines), `tests/` (14 files),
  `examples/`, `docs/` (8 guides), `scripts/docs_qa.py`, `.github/workflows/`
  (`docs-qa`, `tests`), `.aii/config.yaml`, `setup.py`, `pyproject.toml`.

## Phase 1 — Verification battery (before changes)

Environment: Python 3.14.9 venv (`/tmp/atlas-gate-venv`), `pytest` 9.2.0,
`pytest-cov` 7.1.0, `networkx` 3.7, `numpy` 2.5.4.

| Command | Result |
| --- | --- |
| `python3 scripts/docs_qa.py` | passed (whitespace, links/anchors, YAML) |
| `python -m pytest` (core only) | 81 passed, 18 skipped |
| `python -m pytest` with `matplotlib`, `seaborn`, `pandas`, `plotly`, `PyYAML`, `psutil` installed | 1 failed, 98 passed — `tests/test_obsidian_integration.py::TestObsidianParser::test_parse_vault_structure` (templates were also collected as notes) |
| CI on `main` (run 30775470398 / 30775470389) | `docs-qa` and `tests` both green on 2026-08-03 |

Findings by severity:

- **Medium**
  1. `setup.py` and `pyproject.toml` were two packaging homes; `setup.py`
     held all project metadata with stale bounds (`pytest>=6,<8`,
     `flake8<7`, `black<25`, `python_requires>=3.8`).
  2. `python-dateutil` was declared but never imported; `numpy` is used only
     by `atlas.visualization`; `PyYAML` (Obsidian) and `requests` (HTTP
     interface) were used but undeclared.
  3. The Obsidian vault parser recorded `Templates/*.md` as notes as well as
     templates; the test that pins the intended behavior had never run in CI.
- **Minor**
  1. CI ran the core suite only, so 18 tests always skipped.
  2. `tests/run_single_test.py` exposed `test_*` functions returning booleans
     (pytest collection warning).
  3. `actions/checkout@v4` / `actions/setup-python@v5` on deprecated Node 20;
     no workflow `permissions` or timeouts.
  4. README/docs claimed Python 3.8+ and referenced `setup.py`.
- **Not a defect:** the repo has no generative model and no ontology mapping;
  the GNN/AEOS/ontology relation is signposting only.

## Phase 2 — Changes

1. `pyproject.toml` is the only metadata home (PEP 621): `requires-python
   >=3.11`, core `networkx>=3,<4`, extras `viz`, `obsidian`, `http`, `test`,
   `dev`, `all`. `setup.py` removed.
2. `parse_vault` skips `Templates/` when collecting notes; templates are still
   loaded into `vault.templates`.
3. `tests/run_single_test.py` diagnostics renamed to `run_*` so pytest does
   not collect them.
4. CI: `actions/checkout@v7`, `actions/setup-python@v7`, `permissions:
   contents: read`, job timeouts, Python 3.11/3.14 matrix, and
   `pip install -e ".[test,viz,obsidian]"` so no test skips.
5. Docs: new `docs/applied-active-inference.md` (inquiry loop as implemented,
   the honest framing, and the explicit non-claims); README, AGENTS.md,
   `docs/index.md`, `docs/usage.md`, `docs/architecture.md`, `docs/metadata.md`,
   and `docs/quickstart.md` updated for the packaging, dependency, and
   ecosystem changes; sidecar updated (artifacts, relations, `meta.updated`).
6. TO-DO.md and this log record the pass.

## Phase 3 — Verification battery (after changes)

| Command | Result |
| --- | --- |
| `python3 scripts/docs_qa.py` | passed |
| `python -m pytest` with `.[test,viz,obsidian]` | 97 passed, 0 skipped, 0 failed |
| `python -m pytest` with `.[test]` only | 80 passed, 17 skipped (16 Obsidian + 1 visualization; `psutil` now runs the memory test) |
| Clean-venv editable install from `pyproject.toml` | succeeded; `atlas-knowledge` 1.0.0, `Requires: networkx` |
| Python 3.11.17 + 3.14.9 full-suite runs | 97 passed on both |
| `examples/basic/basic_test.py`, `examples/advanced/comprehensive_demo.py` | exit 0 |
| `gh api repos/ActiveInferenceInstitute/ATLAS` (read-only) | repository description and topics verified current; the two steward-action TO-DO items are closed |
| Full suite repeated 6× on Python 3.14 | 97 passed each run |

## Phase 4 — Not run / limits

- No lint gate exists in this repository (`black`, `flake8`, `mypy` are
  declared in the `dev` extra but not wired to CI); none was added, because
  the ported code has not been normalized to any of those tools and inventing
  a gate here would be a policy change, not a currency fix.
- The GNN, AEOS, and ontology claims in the docs are links and pins verified
  against those repositories; no GNN model was authored and no ontology
  identifier mapping was created, because ATLAS has no generative model and
  no vocabulary to map.
- `atlas.visualization` was reviewed for duplication (five modules, parallel
  figure/color-scheme helpers) but not consolidated; recorded as an optional
  open item in TO-DO.md.
