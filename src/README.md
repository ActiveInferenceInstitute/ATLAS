# `src/` — the `atlas` Python package

`src/` uses the src layout: the installable package is `src/atlas/`, so it is
imported as `atlas` after `pip install -e .` and never shadowed by a root-level
directory. Packaging metadata lives in [`../pyproject.toml`](../pyproject.toml).

## Layout

| Module | Role |
| --- | --- |
| [`atlas/__init__.py`](atlas/__init__.py) | Public exports: `ATLASEngine`, `Entity`, `Pattern`, `iQuery`, `PromptInterface`. |
| [`atlas/core/engine.py`](atlas/core/engine.py) | `ATLASEngine` orchestrator (graph, registries, query/export) and `ATLASConfig`. |
| [`atlas/entities/`](atlas/entities/) | `Entity` knowledge items, typed `Attribute`s, anomalies, exceptions, RFIs. |
| [`atlas/patterns/`](atlas/patterns/) | `Pattern` question kits and `PatternEngine` (hierarchy, similarity, clustering, usage). |
| [`atlas/queries/`](atlas/queries/) | `iQuery` discovery lifecycle, results, and quality/confidence scoring. |
| [`atlas/interfaces/`](atlas/interfaces/) | Pluggable transforms: `PromptInterface`, `SimpleTransformInterface`, `HTTPPromptInterface`, factories. |
| [`atlas/integrations/`](atlas/integrations/) | Obsidian vault parsing and conversion (`obsidian` extra). |
| [`atlas/visualization/`](atlas/visualization/) | Graph, network, pattern, metrics, and animation figures (`viz` extra). |
| [`atlas/utils/`](atlas/utils/) | Helpers: id generation, timestamps, deep merge, flatten/unflatten, text utilities, metrics. |

Only `networkx` is a core dependency; the optional imports above belong to the
`viz`, `obsidian`, and `http` extras, so import those modules only when their
extra is installed. The module map and design are documented in
[`../docs/architecture.md`](../docs/architecture.md); the class-by-class API
surface in [`../docs/api.md`](../docs/api.md).
