# ATLAS

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Docs QA](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/docs-qa.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/docs-qa.yml)
[![Tests](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/tests.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/tests.yml)

ATLAS — Adaptive Thinking and Learning Architecture System — is a knowledge
management framework of the Active Inference Institute. It provides
question-oriented information discovery over entities, patterns, and typed
relationships, without requiring shared schemas across domains.

The Institute's public [Open Source Map](https://activeinference.institute/knowledge/)
classifies ATLAS as a *project materials repository* within the
*open-source projects* family. For context, see
[docs/overview.md](docs/overview.md).

## Features

- **Entities and attributes** — knowledge items with typed attributes,
  anomaly/exception tracking, and requests for information (RFIs).
- **Patterns** — reusable question kits with hierarchy, similarity,
  clustering, and usage analysis (`PatternEngine`).
- **Question-oriented queries** — `iQuery` lifecycle with quality and
  confidence scoring.
- **Pluggable interfaces** — simple transforms, HTTP (REST client), and
  identity/format factories.
- **Graph-backed engine** — `networkx` directed graph with relationships,
  metrics, and GraphML/GEXF/JSON export.
- **Optional integrations** — Obsidian vault parsing and visualization
  modules (viz extras).

## Installation

Python 3.11+:

```bash
git clone https://github.com/ActiveInferenceInstitute/ATLAS.git
cd ATLAS
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional extras: `pip install -e ".[viz]"` (visualization), `.[obsidian]`
(vault import/export), `.[http]` (HTTP prompt interface), and `.[test]` (test
suite). `.[all]` installs everything.

## Quick start

```python
from atlas import ATLASEngine
from atlas.core.engine import ATLASConfig

engine = ATLASEngine(config=ATLASConfig())
engine.add_entity("doc1", {"title": "Active Inference", "body": "Free energy principle."})
engine.add_pattern("pat1", {"qkit": ["free energy", "active inference"]})

results = engine.query("active inference")
for r in results:
    print(r["id"], r["type"], r["relevance_score"])
```

See [docs/usage.md](docs/usage.md) for a full walkthrough.

## Tests

```bash
pip install -e ".[test,viz,obsidian]"
python -m pytest
```

The optional extras are installed so the visualization, Obsidian, and
memory-instrumentation tests run instead of skipping.

## Documentation

- [Documentation index](docs/index.md) — all guides in one place.
- [About ATLAS](docs/overview.md) — classification, status, and ecosystem
  context.
- [Architecture](docs/architecture.md) — module map and design.
- [API reference](docs/api.md) — public API, class by class.
- [Usage](docs/usage.md) — install and walkthrough.
- [Applied active inference](docs/applied-active-inference.md) — where the
  inquiry loop matches the active inference framing and where it does not.
- [Metadata reference](docs/metadata.md) — the `.aii` sidecar, field by
  field.
- [Quickstart](docs/quickstart.md) — repository quickstart.

## Repository layout

| Path | Description |
| --- | --- |
| `src/atlas/` | The ATLAS package (engine, entities, patterns, queries, interfaces, integrations, visualization, utils). |
| `tests/` | Test suite (kept green in CI; optional-dependency tests skip without extras). |
| `examples/` | Runnable examples (basic, advanced). |
| `pyproject.toml` | Packaging metadata, dependency extras, and pytest configuration. |
| [README.md](README.md) | This overview. |
| [AGENTS.md](AGENTS.md) | Working conventions for contributors (human and agent). |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute. |
| [CITATION.cff](CITATION.cff) | Machine-readable citation metadata. |
| [LICENSE](LICENSE) | CC-BY-4.0 license text and summary. |
| [SECURITY.md](SECURITY.md) | Security reporting. |
| [docs/](docs/) | Documentation index and guides. |
| [TO-DO.md](TO-DO.md) | Scoped improvements and open items. |
| [scripts/docs_qa.py](scripts/docs_qa.py) | Documentation QA gate (also run in CI). |
| [.github/](.github/) | Issue/PR templates, docs QA and tests workflows. |
| [.aii/config.yaml](.aii/config.yaml) | InstituteOS metadata sidecar. |

## Quality gate

Before opening a pull request, run the documentation QA gate and the test
suite:

```bash
python3 scripts/docs_qa.py
python -m pytest
```

Both run automatically in CI (see the badges above).

## Provenance

The initial implementation was ported from the public reference fork
([docxology/ATLAS](https://github.com/docxology/ATLAS)) on 2026-08-02 and is
distributed under this repository's CC-BY-4.0 license. The fork's own
documentation was not ported: its claims (version/status headers, an
aspirational Web UI and REST API, and assessment artifacts) were unverified
relative to its code. See [docs/overview.md](docs/overview.md) and
[REVIEW_LOG_2026-08-02.md](REVIEW_LOG_2026-08-02.md).

## License

ATLAS is licensed under the
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
license. See [LICENSE](LICENSE) for the full text and a human-readable
summary.

## Citation

If you use or reference this repository, please cite it as:

> Active Inference Institute — ATLAS.

Machine-readable citation metadata is available in
[CITATION.cff](CITATION.cff).

## Links

- Repository: <https://github.com/ActiveInferenceInstitute/ATLAS>
- Active Inference Institute: <https://www.activeinference.org>
- Open Source Map: <https://activeinference.institute/knowledge/>
- InstituteOS (federating metadata): <https://github.com/ActiveInferenceInstitute/InstituteOS>
- GNN — notation and pipeline for specifying, validating, and executing
  active inference generative models:
  <https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation>
  ([integration guides](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/tree/8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1/docs/gnn/integration);
  [downstream adoption guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
  for repositories that consume the notation)
- Active_Inference_Ontology — controlled vocabulary of active inference
  concepts: <https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology>
- AEOS — Active Entity Ontology for Science:
  <https://github.com/ActiveInferenceInstitute/AEOS>

ATLAS carries no generative-model specification and no ontology mapping; the
surfaces above own those contracts. See
[docs/applied-active-inference.md](docs/applied-active-inference.md).
