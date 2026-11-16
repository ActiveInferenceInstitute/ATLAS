# ATLAS API reference

Public API of the `atlas` package (version 1.0.0, license CC-BY-4.0), as
implemented in `src/atlas/`. This reference describes the source contracts;
see [architecture.md](architecture.md) for the module map.

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
| `add_relationship(source_id, target_id, relationship_type)` | Add an explicit relationship occurrence, including repeated identical calls. |
| `query(query_string, context=None)` | Keyword search over entities/patterns/queries; returns ranked result dicts. |
| `get_node(node_id)` | Fetch a node by id. |
| `get_relationships(node_id, relationship_type=None)` | Return all explicit, owned and declaration occurrences as `(target, type)` pairs. |
| `get_metrics()` | Usage and graph metrics (counts, density, components). |
| `export_graph(format='graphml')` | Serialize a detached graph as `graphml`, `gexf`, `json`, `edgelist` or `adjlist`. |
| `clear()` | Clear all graph data. |
| `reconcile_graph()` | Refresh effective edges from current mutable registries; return the live graph. |
| `get_pattern_hierarchy_graph()` | Return detached topology over registered pattern endpoints and effective `parent_of` edges. |
| `replace_owned_relationships(owner, triples)` | Atomically replace one owner's `(source, target, type)` occurrences after endpoint admission. |

Re-registering an ID replaces its node attributes without removing incident
explicit relationships. The public graph remains a `networkx.DiGraph`, including
`graph.edges[source, target]` indexing. Its edge count measures endpoint pairs,
not relationship multiplicity.

Each managed edge's `relationships` list retains occurrence dictionaries with
`relationship_type` and `origin`: `explicit`, `declaration`, or `owned` (with
an `owner` key). The singular `relationship_type` is the last explicit type,
otherwise the last owned or declaration type. One declaration occurrence
represents the union of current hierarchy declarations.

Replacing owned relationships preserves manual occurrences, including identical
types. An empty list withdraws that owner's occurrences; a missing endpoint
returns `False` without replacing the previous owned set.

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

RFI IDs retain `rfi_{entity_id}_{attribute_key}_{uuid_fragment}`. Resolution
matches the receiving entity and final eight-hexadecimal-character suffix,
preserving underscores and empty attribute keys. Malformed or unknown IDs,
removed attributes and unsuccessful writes leave requests pending.

### `entities.attribute.Attribute`
Typed attribute with value, validation rules, linking, transformation
history, and serialization.

## `patterns.pattern` / `patterns.pattern_engine`

### `Pattern`
Question kit management (`add_qkit_item`, `remove_qkit_item`), parent/child
relationships, instances, derivations, `calculate_effectiveness_score`,
`to_dict`/`from_dict`.

`effectiveness_score` is derived state, refreshed by calculation, statistics,
serialization and existing mutators. Direct collection/counter changes and
arbitrary score overrides reconcile at those boundaries; saved scores are not
authoritative.

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


Both registries retain authored `parents` and `children`, including unresolved
references. Effective hierarchy is their union; core additionally includes
explicit `parent_of` occurrences. Replacing a record withdraws only its own
declarations. Reconciliation never mirrors effective edges into authored lists.
Core and `PatternEngine` remain independent registries.

Use `get_pattern_hierarchy_graph()` for detached topology at analysis boundaries.
`PatternEngine` snapshot node attributes still refer to live `Pattern` objects.
Cycles yield `hierarchy_depth=None`; role and usage analysis remain available.
## `queries.iquery`

### `iQuery`
Lifecycle: `start_execution`, `complete_execution`, `fail_execution`,
`cancel_execution`; results (`add_result`, `clear_results`);
prompts (`add_prompt`, `remove_prompt`); context (`set_context`,
`get_context`); scoring (`calculate_quality_score`,
`calculate_confidence_score`); `get_statistics`; serialization.
Enums: `QueryStatus`, `QueryPriority`.

Incremental and bulk ingestion maintain the same derived indexes and scores.
Direct list or nested-result mutations reconcile during scoring, statistics and
serialization. Index sets retain their identities through reconciliation and
clearing; restoration rebuilds them from results rather than trusting saved
indexes or scores. Empty results have zero scores. Terminal scoring uses finalized
execution time; scoring formulas are unchanged.

## `interfaces.prompt_interface`

### `PromptInterface` (base) and subclasses
| Class | Description |
| --- | --- |
| `PromptInterface` | Base: `transform`, `validate_input`, `validate_output`, `execute`, `get_statistics`. |
| `SimpleTransformInterface` | Applies a user-supplied callable. |
| `HTTPPromptInterface` | REST client transform (GET/POST) via `requests`. |

Factories: `create_identity_interface(interface_id=None)`,
`create_format_interface(...)`.

Execution counts each request once and each rejection or caught exception once.
Success rate updates after every terminal outcome. Failure responses retain
`success=False`, error text and `data=None`.

## `integrations.obsidian`

`ObsidianNote`, `ObsidianVault`, `ObsidianParser`, `ObsidianIntegration`,
`ATLASJSONEncoder` — parse and convert Obsidian vault content.
`ObsidianParser.parse_vault` loads `Templates/*.md` into `vault.templates`
and excludes them from `vault.notes`.

Note identity is vault-qualified and source ownership is persisted. Import,
refresh and partial export semantics are detailed in
[usage](usage.md#obsidian-ownership-and-sync).

## `utils.helpers`

`generate_id`, `timestamp_now`, `deep_merge`, `safe_get`, `flatten_dict`,
`unflatten_dict`, `validate_id`, `sanitize_string`, `calculate_metrics`,
`chunk_list`, `normalize_text`.

## Testing

Run the test suite from the repository root:

```bash
./gate setup
./gate test
```
