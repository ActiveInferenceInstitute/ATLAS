# AGENTS.md — working in this repository

ATLAS is a public repository of the Active Inference Institute containing
the ATLAS knowledge management system (Python package in `src/atlas/`),
its tests, examples, documentation, and InstituteOS metadata.

## Ground rules

- **No fabrication.** Everything committed here must be grounded in the
  actual state of the repository or in verifiable public sources (cite
  them). Never invent statistics, links, citations, file paths, or claims.
  Docs must match the code; when they drift, fix the docs or the code to
  the verified reality.
- **No private information.** Never commit local paths, credentials, or
  internal workflow details. This repository is public.
- **Scope.** Keep changes proportionate: fix what exists; do not add
  aspirational features or document systems that are not in this
  repository.

## Layout

- `src/atlas/` — the package (core engine, entities, patterns, queries,
  interfaces, integrations, visualization, utils).
- `tests/` — pytest suite; `examples/` — runnable examples.
- `pyproject.toml` — the only packaging metadata home (project metadata,
  dependency extras, pytest configuration).
- `README.md` — entry point and index; `docs/` — guides, with
  `docs/README.md` as the hub and `docs/documentation-index.md` as the flat
  index (overview, architecture, API, usage, applied active inference,
  metadata, quickstart, gate). Each code folder carries a `README.md`:
  `src/README.md`, `tests/README.md`, and `docs/README.md`.
- `TO-DO.md` — scoped improvements; update it when you complete or add work.
- `REVIEW_LOG_*.md` — audit trail for documentation/implementation passes.
- `.aii/config.yaml` — InstituteOS metadata sidecar (schema: `aii-sidecar/v1`).
- `CITATION.cff`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md` — standard
  repository metadata.
- `gate` — the single gate entry point; `./gate --list` prints every arm with
  its exact command. `.flake8` holds the lint arm's configuration.
- `scripts/docs_qa.py` — the documentation QA gate; `scripts/gnn_conformance.py`
  — the pinned GNN conformance check; `scripts/gate_metrics.py` — writes and
  checks `docs/_generated/GATE.md`.
- `.github/` — issue/PR templates, the `gate` workflow, and the GNN pin
  (`.github/gnn-pin.json`, schema `gnn-importer-pin/v1`).

## Before committing

Install the one environment, then run the gate and fix anything it reports:

```bash
./gate setup
./gate all
```

`all` is the lint arm, the docs arm, and the full test suite; see
[`docs/gate.md`](docs/gate.md). Every arm runs from `./gate` and CI
(`.github/workflows/gate.yml`) calls the same arms — never add a second copy of
a command to a workflow or a doc. The docs arm checks trailing whitespace,
relative links and same-file/cross-file heading anchors in markdown, and YAML parseability of
`.aii/config.yaml` and `CITATION.cff`, then checks that
`docs/_generated/GATE.md` still matches the gate's arm list. The test suite must
stay green; the setup step installs the optional extras, so no test skips. The
`gnn` arm runs separately because it installs the pinned parser: it validates
the pin in `.github/gnn-pin.json` and, as ATLAS defines no `.gnn.md` model file,
the pinned upstream exemplar (see `.github/GNN.md`).

Measured numbers (per-arm wall time, test counts) are generated into
`docs/_generated/GATE.md` by `./gate measure`; do not type them into prose.

## Code conventions

- The package follows the existing style of `src/atlas/`; the `dev` extras
  declare black, flake8, mypy, and pytest tooling. Do not reformat files
  gratuitously.
- Dependencies are declared in `pyproject.toml` only. Core is `networkx`;
  `numpy`, `matplotlib`, `seaborn`, `pandas`, and `plotly` are the `viz`
  extra, `PyYAML` is `obsidian`, `requests` is `http`, and the suite tooling
  is `test`/`dev`.
- Public API changes must be reflected in `docs/api.md` and
  `docs/usage.md`.

## Ecosystem

ATLAS is the discovery layer over knowledge items; it deliberately carries no
generative-model notation and no ontology mapping.

- Generative-model specification: GNN —
  <https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation>,
  integration guides at `docs/gnn/integration/` in the pinned revision
  `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` (v5.0.3).
- Shared controlled vocabulary: Active_Inference_Ontology —
  <https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology>.
- Domain ontology for scientific ecosystems: AEOS —
  <https://github.com/ActiveInferenceInstitute/AEOS>.
- The inquiry-loop framing and its limits are documented in
  `docs/applied-active-inference.md`; do not strengthen its claims without
  evidence from the code.

## Metadata conventions

- The `.aii` sidecar follows the InstituteOS `aii-sidecar/v1` schema; see
  `docs/metadata.md` and the InstituteOS schema documentation. Only change
  it with values true of this repository.
- License is CC-BY-4.0; contributions are licensed accordingly (see
  `CONTRIBUTING.md`).
