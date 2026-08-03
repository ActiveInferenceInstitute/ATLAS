# AGENTS.md — working in this repository

ATLAS is a public, documentation-only repository of the Active Inference
Institute. It currently contains metadata and documentation; there is no
code, build system, or test suite.

## Ground rules

- **No fabrication.** Everything committed here must be grounded in the
  actual state of the repository or in verifiable public sources (cite
  them). Never invent statistics, links, citations, file paths, or claims.
- **No private information.** Never commit local paths, credentials, or
  internal workflow details. This repository is public.
- **Documentation-facing.** Keep content proportionate: describe what
  exists; do not write guides for systems that are not in this repository.

## Layout

- `README.md` — entry point and index.
- `docs/` — guides: index, overview, metadata reference, quickstart.
- `TO-DO.md` — scoped improvements; update it when you complete or add work.
- `REVIEW_LOG_*.md` — audit trail for documentation passes.
- `.aii/config.yaml` — InstituteOS metadata sidecar (schema: `aii-sidecar/v1`).
- `CITATION.cff`, `CONTRIBUTING.md`, `LICENSE`, `SECURITY.md` — standard
  repository metadata.
- `scripts/docs_qa.py` — the documentation QA gate.
- `.github/` — issue/PR templates and the `docs-qa` CI workflow.

## Before committing

Run the QA gate and fix anything it reports:

```bash
python3 scripts/docs_qa.py
```

The same gate runs as CI (`.github/workflows/docs-qa.yml`). It checks
trailing whitespace, relative links and in-file anchors in markdown, and
YAML parseability of `.aii/config.yaml` and `CITATION.cff`.

## Metadata conventions

- The `.aii` sidecar follows the InstituteOS `aii-sidecar/v1` schema; see
  `docs/metadata.md` and the InstituteOS schema documentation. Only change
  it with values true of this repository.
- License is CC-BY-4.0; contributions are licensed accordingly (see
  `CONTRIBUTING.md`).
