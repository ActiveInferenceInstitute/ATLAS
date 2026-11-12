# ATLAS

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Gate](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/gate.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/ATLAS/actions/workflows/gate.yml)

ATLAS — Adaptive Thinking and Learning Architecture System — is a knowledge
management framework of the Active Inference Institute. It provides
question-oriented information discovery over entities, patterns, and typed
relationships, without requiring shared schemas across domains.

The Institute's public [Open Source Map](https://activeinference.institute/knowledge/)
classifies ATLAS as a *project materials repository* within the
*open-source projects* family. For context, see
[docs/overview.md](docs/overview.md).

## Contents

- [Status](#status)
- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Tests](#tests)
- [Documentation](#documentation)
- [Repository layout](#repository-layout)
- [Quality gate](#quality-gate)
- [Provenance](#provenance)
- [License](#license)
- [Citation](#citation)
- [Links](#links)

## Status

Active, released as v1.0.0. The core engine, entities, patterns, queries, and
interfaces run locally and offline with only `networkx` installed. The optional
`viz`, `obsidian`, and `http` extras add visualization, vault import/export, and
an HTTP client; the tests that use them skip when the extra is absent. The GNN
conformance arm (`./gate gnn`) installs the parser pinned in
[`.github/gnn-pin.json`](.github/gnn-pin.json) at run time and needs network
access. See [`TO-DO.md`](TO-DO.md) for the known warning-sentinel caveat in that
arm and the open optional items.

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

The repository has one gate with separately runnable arms — see
[`docs/gate.md`](docs/gate.md):

```bash
./gate setup   # one environment for the lint and test arms
./gate         # fast arm: the suite without the `slow` marker
./gate test    # full suite
./gate all     # lint, docs, test
```

The gate installs the optional extras, so the visualization, Obsidian, and
memory-instrumentation tests run instead of skipping.

## Documentation

- [Documentation hub](docs/README.md) and [documentation index](docs/documentation-index.md)
  — every long-lived document in one place.
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
- [The gate](docs/gate.md) — arms, CI mapping, and the measured per-arm page.
- [src/README.md](src/README.md) and [tests/README.md](tests/README.md) —
  folder guides for the package and test trees. The measured per-arm numbers
  live in [docs/_generated/GATE.md](docs/_generated/GATE.md).

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
| [gate](gate) | The single gate entry point; `./gate --list` prints every arm. |
| [.flake8](.flake8) | Lint arm configuration (fatal-error codes only). |
| [scripts/docs_qa.py](scripts/docs_qa.py) | Documentation QA gate (the `docs` arm). |
| [scripts/gnn_conformance.py](scripts/gnn_conformance.py) | Pinned GNN conformance (the `gnn` arm). |
| [scripts/gate_metrics.py](scripts/gate_metrics.py) | Measures the arms into `docs/_generated/GATE.md`. |
| [.github/](.github/) | Issue/PR templates, the `gate` workflow, and the GNN pin. |
| [.aii/config.yaml](.aii/config.yaml) | InstituteOS metadata sidecar. |

## Quality gate

Before opening a pull request, run the gate:

```bash
./gate all
```

`all` is lint, documentation QA, and the full test suite. The `gnn` arm
(`./gate gnn`) additionally needs network access and runs in its own CI job.
Every arm runs from one entry point and CI calls the same arms; see
[`docs/gate.md`](docs/gate.md) and the badge above.

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
