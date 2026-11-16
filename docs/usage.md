# Usage

How to install and use the ATLAS knowledge management system.

## Installation

ATLAS requires Python 3.11+ and uses a `src/` layout with packaging metadata
in `pyproject.toml`:

```bash
git clone https://github.com/ActiveInferenceInstitute/ATLAS.git
cd ATLAS
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional extras:

| Extra | Adds | For |
| --- | --- | --- |
| `viz` | `matplotlib`, `seaborn`, `pandas`, `plotly`, `numpy` | `atlas.visualization` |
| `obsidian` | `PyYAML` | `atlas.integrations.obsidian` |
| `http` | `requests` | `HTTPPromptInterface` |
| `test` | `pytest`, `pytest-cov`, `psutil` | the test suite |
| `dev` | `black`, `flake8`, `mypy`, and the test tooling | contributors |

```bash
pip install -e ".[viz]"
pip install -e ".[test,viz,obsidian]"   # what ./gate setup installs
```

## Quick start

The following snippet exercises the core API (verified against the current
code):

```python
from atlas import ATLASEngine
from atlas.core.engine import ATLASConfig

engine = ATLASEngine(config=ATLASConfig())
engine.add_entity("doc1", {"title": "Active Inference", "body": "Free energy principle."})
engine.add_pattern("pat1", {"qkit": ["free energy", "active inference"]})

results = engine.query("active inference")
for r in results:
    print(r["id"], r["type"], r["relevance_score"])
# doc1 entity 1.0
# pat1 pattern 0.0

print(engine.get_metrics())
```

`engine.query()` performs keyword matching over registered entities,
patterns, and queries and returns results ranked by relevance score.

## Working with entities

```python
from atlas import Entity

entity = Entity(entity_id="e1")
entity.add_attribute("topic", "active inference")
entity.add_pattern("pat1")
entity.mark_anomaly("q1", "unresolved term")
print(entity.get_anomalies())
```

## Working with patterns

```python
from atlas import Pattern
from atlas.patterns.pattern_engine import PatternEngine

pattern = Pattern(pattern_id="p1", qkit=["free energy", "variational"])
engine = PatternEngine()
engine.add_pattern(pattern)
print(engine.get_statistics())
```

## Working with queries

```python
from atlas import iQuery
from atlas.queries.iquery import QueryPriority

query = iQuery(
    query_id="q1",
    query_text="What is free energy?",
    target_patterns=["p1"],
    priority=QueryPriority.HIGH,
)
query.start_execution()
query.add_result({"answer": "..."})
query.complete_execution()
print(query.calculate_quality_score())
```

## Serialization and graph export

Entities, patterns, and queries support `to_dict()`/`from_dict()`.
`ATLASEngine.export_graph()` serializes the whole graph:

```python
graphml = engine.export_graph(format="graphml")  # also gexf, json, edgelist, adjlist
```

Serialization uses a detached graph, leaving live records unchanged. XML omits
top-level null attributes and JSON-encodes structured values, retaining nested
nulls; dates become ISO strings and sets become arrays. JSON retains native
null/list/dictionary structure. XML views are not typed round-trip formats.
Relationship occurrence lists are retained as JSON text in XML. An empty
string signals export failure.

`GraphVisualizer.export_graph_formats(base_path)` uses that serializer for
GraphML, GEXF, edge-list and adjacency-list files and returns only successful
paths. A partial mapping is partial output; an empty mapping is failure.
Successful files survive another format's failure. Consumers requiring complete
export must require all four keys and readable files. Adjacency lists describe
topology only; use JSON or XML for occurrence data.

## Obsidian ownership and sync

Note keys are extensionless relative paths, namespaced by the resolved vault
root. Moving a vault root creates a distinct namespace unless an existing
identity can be explicitly associated. Ambiguous legacy mappings fail rather
than guessing.

Persisted `obsidian` ownership fields are `vault_path`, `note_id`,
`attribute_keys`, `pattern_ids`, `tags`, `attribute_tags` and `metadata_tags`.
The latter two track source ownership independently, so a source tag that
overlaps an existing manual tag does not claim or later remove the manual value.
Refresh updates source title,
content, path, wiki-links, dates and frontmatter; content retains the
1000-character preview limit. Unrelated manual state survives. Legacy core
fields and the `fm_` namespace are treated as source fields, but unowned legacy
relationships are not retroactively claimed.

Source-owned relationships are replaced per note, not appended on every sync;
manual occurrences survive even when their types match. Missing or unreadable
notes are not deleted or withdrawn, and readable peers continue. Conflicts with
new manual fields refuse only that note's refresh.

Import statistics include `entities_updated`. `relationships_created` counts
refreshed source occurrences, not net graph growth. Import/export errors remain
strings; parser errors are keyed by relative path. Malformed YAML is tolerated
rather than classified as a failed read.

`atlas_export` frontmatter is reserved. Known generated entity/pattern views and
indexes are excluded from sync import; exported entity notes remain importable
into a fresh engine. Ordinary existing notes and indexes are reserved, not
overwritten; previous generated files may be reused, and stale files are not
deleted.

Exports allocate vault-qualified links. Individual write failures remain errors,
and indexes list only successful writes. Already-written notes may reference a
planned target whose write failed: errors preclude a complete-export claim.

## Visualization state and simulations

An empty overview explicitly reports no component data; the default empty report
still produces charts and JSON. Overview layout reserves space for adjacent
titles and axis labels. Simulated activity/performance panels remain labeled
as simulations, not observations.

Visualization simulations preserve callers' global NumPy random state, retaining
the existing seeded samples and scientific/heuristic formulas. Query randomness
is local and graph layouts use explicit seeds. Directed animation-frame density
describes the actual frame graph; simulated system metrics remain a separate
heuristic.

Network views reconcile current graph state before analysis. Hierarchy views and
animations use effective mutable declarations and explicit `parent_of`
relationships. Inheritance `max_depth` is inclusive shortest-path edge distance:
zero shows the root, and cycles remain visible among included nodes.

## Running the tests

```bash
./gate setup   # installs the extras the suite exercises
./gate test    # full suite
```

`./gate` with no argument runs the fast arm instead: the suite without the
`slow` marker (`tests/test_atlas_performance.py`). The suite is kept green in
CI; with those extras installed no test skips. See [gate.md](gate.md).

## Examples

See [examples/](../examples/) for runnable scripts
(`basic/basic_test.py`, `advanced/comprehensive_demo.py`).
