# ATLAS architecture

This page describes the architecture of the ATLAS knowledge management
system as implemented in this repository (`src/atlas/`). Every module and
method name below refers to the actual code.

## Design overview

ATLAS is a knowledge management framework built around four primitives —
entities, patterns, queries, and interfaces — orchestrated by a central
engine:

- **Engine** (`core/engine.py`) — `ATLASEngine` is the orchestrator. It
  maintains a directed graph (`networkx.DiGraph`) of entities and
  relationships plus registries for entities, patterns, queries, attributes,
  and interfaces. Public methods: `add_entity`, `add_pattern`, `add_query`,
  `add_relationship`, `query`, `get_node`, `get_relationships`,
  `get_metrics`, `export_graph`, `clear`. Behavior is configured through
  `ATLASConfig` (pattern inference, dynamic typing, expansion depth,
  quality metrics, log level).
- **Entities** (`entities/`) — `Entity` represents a knowledge item with
  typed `Attribute`s. Entities track anomalies, exceptions, and requests
  for information (RFIs), and support serialization (`to_dict`/`from_dict`).
- **Patterns** (`patterns/`) — `Pattern` is a reusable question kit (qkit)
  with parent/child, instance, and derivation relationships.
  `PatternEngine` manages pattern hierarchies, similarity calculations,
  clustering, merge suggestions, usage analysis, and hierarchy
  optimization.
- **Queries** (`queries/`) — `iQuery` implements question-oriented
  discovery with a full lifecycle (`start_execution`, `complete_execution`,
  `fail_execution`, `cancel_execution`), result and prompt management,
  context, and quality/confidence scoring.
- **Interfaces** (`interfaces/`) — pluggable data transforms:
  `PromptInterface` (base), `SimpleTransformInterface` (function-backed),
  `HTTPPromptInterface` (REST client), plus factory helpers
  (`create_identity_interface`, `create_format_interface`).
- **Integrations** (`integrations/obsidian.py`) — Obsidian vault handling:
  `ObsidianNote`, `ObsidianVault`, `ObsidianParser`,
  `ObsidianIntegration`.
- **Visualization** (`visualization/`) — graph, network, pattern, metrics,
  and animation visualizations built on optional dependencies
  (`pip install -e ".[viz]"`).
- **Utilities** (`utils/helpers.py`) — id generation, timestamps, deep
  merge, flatten/unflatten, safe get, text normalization, metrics, and
  chunking helpers.

## Component interactions

- `ATLASEngine` owns the graph and registries; entities, patterns, and
  queries are added through it and stored both as registry entries and as
  graph nodes.
- `engine.query()` performs keyword matching over registered entities,
  patterns, and queries, ranks matches by a relevance score, and returns
  result dicts.
- `iQuery` targets patterns and collects results; quality and confidence
  scores summarize each query's execution.
- `PatternEngine` operates on `Pattern` objects independently of the engine
  (hierarchy, similarity, clustering).
- Interfaces transform data in and out of the system; the engine's prompt
  interface is pluggable via the interface registry.

## Data model

- Nodes: entities, patterns, and queries (stored as graph nodes with their
  data as attributes).
- Edges: typed relationships added via `add_relationship` (the engine also
  records implicit pattern/entity links).
- `export_graph` serializes the graph to GraphML, GEXF, or JSON;
  non-scalar attribute values are JSON-encoded for GraphML/GEXF.

## Dependencies

Core: `networkx`, `numpy`, `python-dateutil`. Optional: visualization
extras (`matplotlib`, `seaborn`, `pandas`, `plotly`). See
[`setup.py`](../setup.py) and [`pyproject.toml`](../pyproject.toml).
