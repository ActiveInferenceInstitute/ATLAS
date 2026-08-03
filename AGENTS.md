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
- `README.md` — entry point and index; `docs/` — guides (index, overview,
  architecture, API, usage, metadata, quickstart).
- `TO-DO.md` — scoped improvements; update it when you complete or add work.
- `REVIEW_LOG_*.md` — audit trail for documentation/implementation passes.
- `.aii/config.yaml` — InstituteOS metadata sidecar (schema: `aii-sidecar/v1`).
- `CITATION.cff`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md` — standard
  repository metadata.
- `scripts/docs_qa.py` — the documentation QA gate.
- `.github/` — issue/PR templates, `docs-qa` and `tests` CI workflows.

## Before committing

Run both gates and fix anything they report:

```bash
python3 scripts/docs_qa.py
python -m pytest
```

The same gates run as CI (`.github/workflows/docs-qa.yml` and
`.github/workflows/tests.yml`). The QA gate checks trailing whitespace,
relative links and in-file anchors in markdown, and YAML parseability of
`.aii/config.yaml` and `CITATION.cff`. The test suite must stay green
(optional-dependency tests may skip when extras are not installed).

## Code conventions

- The package follows the existing style of `src/atlas/`; the `dev` extras
  declare black, flake8, mypy, and pytest tooling. Do not reformat files
  gratuitously.
- Core dependencies stay minimal (`networkx`, `numpy`, `python-dateutil`);
  optional features go in the `viz` extras.
- Public API changes must be reflected in `docs/api.md` and
  `docs/usage.md`.

## Metadata conventions

- The `.aii` sidecar follows the InstituteOS `aii-sidecar/v1` schema; see
  `docs/metadata.md` and the InstituteOS schema documentation. Only change
  it with values true of this repository.
- License is CC-BY-4.0; contributions are licensed accordingly (see
  `CONTRIBUTING.md`).
