# `tests/` — pytest suite

The suite runs with `pytest` from the repository root after installing the
dependency extras the tests exercise, so no test skips:

```bash
pip install -e ".[test,viz,obsidian]"
python -m pytest
```

| Test file | Covers |
| --- | --- |
| [`unit/test_entity_unit.py`](unit/test_entity_unit.py) | `Entity` and `Attribute` unit behavior. |
| [`integration/test_atlas_workflow.py`](integration/test_atlas_workflow.py) | End-to-end engine/query/pattern workflow. |
| [`test_atlas_system.py`](test_atlas_system.py) | Engine and system-level behavior. |
| [`test_atlas_comprehensive.py`](test_atlas_comprehensive.py) | Broad coverage of the public API. |
| [`test_atlas_performance.py`](test_atlas_performance.py) | Bounded performance and scaling checks (uses `psutil`). |
| [`test_comprehensive_coverage.py`](test_comprehensive_coverage.py) | Additional coverage of edge paths. |
| [`test_comprehensive_visualization_suite.py`](test_comprehensive_visualization_suite.py) | `atlas.visualization` figures (`viz` extra). |
| [`test_obsidian_integration.py`](test_obsidian_integration.py) | Obsidian parsing and conversion (`obsidian` extra). |
| [`test_config.py`](test_config.py) | `ATLASConfig` and engine configuration. |
| [`test_edge_cases.py`](test_edge_cases.py) | Edge cases and error handling. |
| [`run_single_test.py`](run_single_test.py), [`test_runner_simple.py`](test_runner_simple.py) | Standalone runners for a single test, not collected as test modules. |

[`fixtures/`](fixtures/) holds shared fixtures. Tests that need an optional
extra skip when it is not installed; CI installs `.[test,viz,obsidian]` so
nothing skips there. The suite needs no network service.
