"""Real network visualization contracts for current topology and local RNG."""

from copy import deepcopy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest
from matplotlib.figure import Figure

from atlas.core.engine import ATLASEngine
from atlas.visualization.network_viz import NetworkVisualizer


_CALLS = [
    pytest.param("analyze_network_structure", {}, id="analysis"),
    pytest.param(
        "visualize_centrality_analysis", {"centrality_type": "degree"},
        id="degree",
    ),
    pytest.param(
        "visualize_centrality_analysis", {"centrality_type": "betweenness"},
        id="betweenness",
    ),
    pytest.param(
        "visualize_centrality_analysis", {"centrality_type": "closeness"},
        id="closeness",
    ),
    pytest.param(
        "visualize_centrality_analysis", {"centrality_type": "eigenvector"},
        id="eigenvector",
    ),
    pytest.param("visualize_community_structure", {}, id="communities"),
    pytest.param(
        "visualize_network_evolution", {"time_steps": 4}, id="evolution"
    ),
    pytest.param("export_network_analysis", {}, id="export"),
]


@pytest.fixture
def engine():
    atlas = ATLASEngine()
    for pattern_id in ("root", "middle", "leaf", "side"):
        assert atlas.add_pattern(
            pattern_id, {"parents": [], "children": [], "qkit": []}
        )
    return atlas


@pytest.fixture
def drawn_graphs(monkeypatch):
    """Capture inputs without replacing the real NetworkX drawing work."""
    graphs = []
    draw_edges = nx.draw_networkx_edges

    def capture_edges(graph, *args, **kwargs):
        graphs.append(graph.copy())
        return draw_edges(graph, *args, **kwargs)

    monkeypatch.setattr(nx, "draw_networkx_edges", capture_edges)
    return graphs


def _declare_current_edges(engine):
    engine.patterns["root"]["children"].extend(["middle", "side"])
    engine.patterns["middle"]["children"].append("leaf")
    engine.patterns["leaf"]["children"].append("root")
    engine.patterns["side"]["children"].append("root")
    return {
        ("root", "middle"), ("root", "side"),
        ("middle", "leaf"), ("leaf", "root"), ("side", "root"),
    }


def _invoke(visualizer, method, kwargs, output_base):
    arguments = dict(kwargs)
    if method == "export_network_analysis":
        arguments["output_path"] = str(output_base)
    result = getattr(visualizer, method)(**arguments)
    if isinstance(result, Figure):
        try:
            result.canvas.draw()
            assert result.axes
            assert any(axis.collections for axis in result.axes)
        finally:
            plt.close(result)
    else:
        assert "error" not in result
        assert result["basic_metrics"]["nodes"] == 4
        if method == "export_network_analysis":
            saved = json.loads(
                Path(f"{output_base}_network_analysis.json").read_text(
                    encoding="utf-8"
                )
            )
            assert saved["basic_metrics"] == result["basic_metrics"]
            paths = result["visualizations_generated"]
            assert len(paths) == 3
            for path in paths:
                pixels = plt.imread(path)
                assert pixels.ndim == 3
                assert pixels.shape[0] > 0 and pixels.shape[1] > 0
                assert np.ptp(pixels[..., :3]) > 0
    return result


@pytest.mark.parametrize(("method", "kwargs"), _CALLS)
def test_public_network_calls_reconcile_direct_mutations(
    engine, drawn_graphs, tmp_path, method, kwargs
):
    visualizer = NetworkVisualizer(engine)
    expected = _declare_current_edges(engine)
    authored = deepcopy(engine.patterns)
    assert not engine.graph.edges

    result = _invoke(visualizer, method, kwargs, tmp_path / "before")
    assert set(engine.graph.edges) == expected
    assert engine.patterns == authored
    if isinstance(result, dict):
        assert result["basic_metrics"]["edges"] == len(expected)
        assert result["basic_metrics"]["density"] == pytest.approx(5 / 12)
    for graph in drawn_graphs:
        assert set(graph) == set(engine.patterns)
        if graph.is_directed():
            assert set(graph.edges) == expected
        else:
            assert {frozenset(edge) for edge in graph.edges} == {
                frozenset(edge) for edge in expected
            }
    if method != "analyze_network_structure":
        assert drawn_graphs

    # Withdraw a declaration after the first analysis; do not call a core
    # reconciliation method on behalf of the visualizer.
    engine.patterns["root"]["children"].remove("side")
    expected.remove(("root", "side"))
    authored = deepcopy(engine.patterns)
    drawn_graphs.clear()
    result = _invoke(visualizer, method, kwargs, tmp_path / "after")
    assert set(engine.graph.edges) == expected
    assert engine.patterns == authored
    if isinstance(result, dict):
        assert result["basic_metrics"]["edges"] == len(expected)
    for graph in drawn_graphs:
        if graph.is_directed():
            assert set(graph.edges) == expected
        else:
            assert {frozenset(edge) for edge in graph.edges} == {
                frozenset(edge) for edge in expected
            }


@pytest.mark.parametrize(("method", "kwargs"), _CALLS)
def test_complete_network_calls_preserve_global_numpy_state(
    engine, tmp_path, method, kwargs
):
    expected_edges = _declare_current_edges(engine)
    visualizer = NetworkVisualizer(engine)
    before = np.random.get_state()
    comparison = np.random.RandomState()
    comparison.set_state(before)
    expected_draws = comparison.random_sample(5)

    try:
        _invoke(visualizer, method, kwargs, tmp_path / "network")
        assert set(engine.graph.edges) == expected_edges
        after = np.random.get_state()
        assert after[0] == before[0]
        np.testing.assert_array_equal(after[1], before[1])
        assert after[2:] == before[2:]
        np.testing.assert_array_equal(
            np.random.random_sample(5), expected_draws
        )
    finally:
        np.random.set_state(before)
