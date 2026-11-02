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
pip install -e ".[test,viz,obsidian]"   # full suite, nothing skipped
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
graphml = engine.export_graph(format="graphml")  # or "gexf" / "json"
```

## Running the tests

```bash
pip install -e ".[test,viz,obsidian]"
python -m pytest
```

The suite is kept green in CI; with those extras installed no test skips.

## Examples

See [examples/](../examples/) for runnable scripts
(`basic/basic_test.py`, `advanced/comprehensive_demo.py`).
