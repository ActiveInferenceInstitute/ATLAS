# ATLAS API reference

Public API of the `atlas` package (version 1.0.0, license CC-BY-4.0), as
implemented in `src/atlas/`. This reference is generated from the actual
code; see [architecture.md](architecture.md) for the module map.

## Package exports (`src/atlas/__init__.py`)

```python
from atlas import ATLASEngine, Entity, Pattern, iQuery, PromptInterface
```

## `core.engine`

### `ATLASConfig`
Dataclass configuration: `auto_pattern_inference`, `enable_dynamic_typing`,
`max_expansion_depth`, `enable_quality_metrics`, `log_level`.

### `ATLASEngine`
| Method | Description |
| --- | --- |
| `add_entity(entity_id, entity_data)` | Register an entity with its data. |
| `add_pattern(pattern_id, pattern_data)` | Register a pattern. |
| `add_query(query_id, query_data)` | Register a query. |
| `add_relationship(source_id, target_id, relationship_type)` | Add a typed edge. |
| `query(query_string, context=None)` | Keyword search over entities/patterns/queries; returns ranked result dicts. |
| `get_node(node_id)` | Fetch a node by id. |
| `get_relationships(node_id, relationship_type=None)` | Fetch edges for a node. |
| `get_metrics()` | Usage and graph metrics (counts, density, components). |
| `export_graph(format='graphml'|'gexf'|'json')` | Serialize the graph. |
| `clear()` | Clear all graph data. |

## `entities.entity`

### `Entity`
| Method | Description |
| --- | --- |
| `add_attribute(key, value, overwrite=True)` / `get_attribute` / `has_attribute` / `remove_attribute` | Typed attribute management. |
| `add_pattern(pattern_id)` / `has_pattern` / `remove_pattern` | Pattern membership. |
| `mark_anomaly(iquery_id, reason)` / `get_anomalies()` | Anomaly tracking. |
| `mark_exception(iquery_id, reason)` / `get_exceptions()` | Exception tracking. |
| `call_rfis()` / `get_pending_rfis()` / `resolve_rfi(rfi_id, value)` | Requests for information. |
| `to_dict()` / `from_dict(data)` | Serialization. |

### `entities.attribute.Attribute`
Typed attribute with value, validation rules, linking, transformation
history, and serialization.

## `patterns.pattern` / `patterns.pattern_engine`

### `Pattern`
Question kit management (`add_qkit_item`, `remove_qkit_item`), parent/child
relationships, instances, derivations, `calculate_effectiveness_score`,
`to_dict`/`from_dict`.

### `PatternEngine`
| Method | Description |
| --- | --- |
| `add_pattern` / `remove_pattern` | Pattern registry. |
| `get_pattern_hierarchy(pattern_id)` | Parent/child structure. |
| `calculate_pattern_similarity(p1, p2)` / `find_similar_patterns(pattern_id, threshold)` | Similarity. |
| `detect_pattern_clusters(similarity_threshold)` | Clustering. |
| `suggest_pattern_merges(similarity_threshold)` | Merge suggestions. |
| `analyze_pattern_usage()` | Usage statistics. |
| `optimize_pattern_hierarchy()` | Hierarchy optimization. |
| `get_statistics()` | Aggregate statistics. |

## `queries.iquery`

### `iQuery`
Lifecycle: `start_execution`, `complete_execution`, `fail_execution`,
`cancel_execution`; results (`add_result`, `clear_results`);
prompts (`add_prompt`, `remove_prompt`); context (`set_context`,
`get_context`); scoring (`calculate_quality_score`,
`calculate_confidence_score`); `get_statistics`; serialization.
Enums: `QueryStatus`, `QueryPriority`.

## `interfaces.prompt_interface`

### `PromptInterface` (base) and subclasses
| Class | Description |
| --- | --- |
| `PromptInterface` | Base: `transform`, `validate_input`, `validate_output`, `execute`, `get_statistics`. |
| `SimpleTransformInterface` | Applies a user-supplied callable. |
| `HTTPPromptInterface` | REST client transform (GET/POST) via `requests`. |

Factories: `create_identity_interface(interface_id=None)`,
`create_format_interface(...)`.

## `integrations.obsidian`

`ObsidianNote`, `ObsidianVault`, `ObsidianParser`, `ObsidianIntegration`,
`ATLASJSONEncoder` — parse and convert Obsidian vault content.

## `utils.helpers`

`generate_id`, `timestamp_now`, `deep_merge`, `safe_get`, `flatten_dict`,
`unflatten_dict`, `validate_id`, `sanitize_string`, `calculate_metrics`,
`chunk_list`, `normalize_text`.

## Testing

Run the test suite from the repository root:

```bash
pip install -e . pytest pytest-cov
python -m pytest
```
