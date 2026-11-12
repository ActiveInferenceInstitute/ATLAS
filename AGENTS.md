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
- `README.md` — entry point and index; `docs/` — guides (index, overview,
  architecture, API, usage, applied active inference, metadata, quickstart).
  Each code folder carries a `README.md`: `src/README.md`, `tests/README.md`,
  and `docs/README.md`.
- `TO-DO.md` — scoped improvements; update it when you complete or add work.
- `REVIEW_LOG_*.md` — audit trail for documentation/implementation passes.
- `.aii/config.yaml` — InstituteOS metadata sidecar (schema: `aii-sidecar/v1`).
- `CITATION.cff`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md` — standard
  repository metadata.
- `scripts/docs_qa.py` — the documentation QA gate.
- `.github/` — issue/PR templates, `docs-qa` and `tests` CI workflows.

## Before committing

Install the package with the extras the suite exercises, then run both gates
and fix anything they report:

```bash
pip install -e ".[test,viz,obsidian]"
python3 scripts/docs_qa.py
python -m pytest
```

The same gates run as CI (`.github/workflows/docs-qa.yml` and
`.github/workflows/tests.yml`). The QA gate checks trailing whitespace,
relative links and in-file anchors in markdown, and YAML parseability of
`.aii/config.yaml` and `CITATION.cff`. The test suite must stay green; with
the extras above no test skips, and optional-dependency tests skip only when
their extra is absent. `tests.yml` also runs the pinned GNN conformance baseline
(see `.github/GNN.md`); ATLAS defines no `.gnn.md` model file, so the job validates
the pinned upstream exemplar.

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
