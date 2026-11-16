"""Rendered pattern topology and local-randomness contracts (Agg backend)."""

from copy import deepcopy

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest
from matplotlib.figure import Figure

from atlas.core.engine import ATLASEngine
from atlas.patterns.pattern import Pattern
from atlas.patterns.pattern_engine import PatternEngine
from atlas.visualization.pattern_viz import PatternVisualizer


@pytest.fixture
def drawn_graphs(monkeypatch):
    """Observe topology while still executing the real NetworkX renderer."""
    graphs = []
    draw_edges = nx.draw_networkx_edges

    def capture_edges(graph, *args, **kwargs):
        graphs.append(graph.copy())
        return draw_edges(graph, *args, **kwargs)

    monkeypatch.setattr(nx, "draw_networkx_edges", capture_edges)
    return graphs


def _add(engine, pattern):
    assert engine.add_pattern(pattern.id, pattern.to_dict())


def _render(visualizer, view, **kwargs):
    before = deepcopy(visualizer.atlas_engine.patterns)
    if view == "hierarchy":
        figure = visualizer.visualize_pattern_hierarchy(
            layout="circular", **kwargs
        )
    else:
        figure = visualizer.visualize_pattern_inheritance_tree(
            "root", **kwargs
        )
    try:
        assert isinstance(figure, Figure)
        figure.canvas.draw()
        assert figure.axes[0].collections
        assert visualizer.atlas_engine.patterns == before
    finally:
        plt.close(figure)


@pytest.mark.parametrize("view", ["hierarchy", "inheritance"])
@pytest.mark.parametrize("declaration", ["parents", "children"])
@pytest.mark.parametrize("child_first", [False, True])
def test_views_use_late_effective_edges_without_authored_list_changes(
    view, declaration, child_first, drawn_graphs, tmp_path
):
    root = Pattern(pattern_id="root", qkit=["root-question"])
    child = Pattern(pattern_id="child", qkit=["child-question"])
    if declaration == "parents":
        child.parents.append("root")
    else:
        root.children.append("child")
    engine = ATLASEngine()
    first, second = (child, root) if child_first else (root, child)
    _add(engine, first)
    assert set(engine.graph) == {first.id}
    _add(engine, second)
    output = tmp_path / "hierarchy.png"

    _render(PatternVisualizer(engine), view, save_path=str(output))

    graph = drawn_graphs[-1]
    assert set(graph) == {"root", "child"}
    assert set(graph.edges) == {("root", "child")}
    pixels = plt.imread(output)
    assert pixels.ndim == 3
    assert pixels.shape[0] > 0 and pixels.shape[1] > 0
    assert np.ptp(pixels[..., :3]) > 0
    assert engine.patterns["root"]["children"] == root.children
    assert engine.patterns["child"]["parents"] == child.parents


@pytest.mark.parametrize("view", ["hierarchy", "inheritance"])
def test_views_reconcile_replacements_and_direct_mutations(view, drawn_graphs):
    engine = ATLASEngine()
    _add(engine, Pattern(pattern_id="root", children=["old", "missing"]))
    _add(engine, Pattern(pattern_id="old"))
    _add(engine, Pattern(pattern_id="new"))
    visualizer = PatternVisualizer(engine)

    _render(visualizer, view)
    assert set(drawn_graphs[-1].edges) == {("root", "old")}
    assert "missing" not in drawn_graphs[-1]

    _add(engine, Pattern(pattern_id="root", children=["new"]))
    _render(visualizer, view)
    assert set(drawn_graphs[-1].edges) == {("root", "new")}

    engine.patterns["old"]["parents"].append("root")
    _render(visualizer, view)
    assert set(drawn_graphs[-1].edges) == {
        ("root", "old"), ("root", "new")
    }

    engine.patterns["root"]["children"].clear()
    _render(visualizer, view)
    assert set(drawn_graphs[-1].edges) == {("root", "old")}
    _add(engine, Pattern(pattern_id="old"))
    _render(visualizer, view)
    assert not drawn_graphs[-1].edges
    expected = {"root", "old", "new"} if view == "hierarchy" else {"root"}
    assert set(drawn_graphs[-1]) == expected


@pytest.mark.parametrize("view", ["hierarchy", "inheritance"])
def test_views_retain_explicit_hierarchy_hidden_by_another_type(
    view, drawn_graphs
):
    engine = ATLASEngine()
    for pattern_id in ("root", "child", "unrelated"):
        _add(engine, Pattern(pattern_id=pattern_id))
    assert engine.add_relationship("root", "child", "parent_of")
    assert engine.add_relationship("root", "child", "related_to")
    assert engine.add_relationship("root", "unrelated", "related_to")
    assert engine.graph.edges["root", "child"]["relationship_type"] == (
        "related_to"
    )
    assert engine.add_entity("entity", {"attributes": {}})
    assert engine.add_relationship("root", "entity", "parent_of")

    _render(PatternVisualizer(engine), view)

    graph = drawn_graphs[-1]
    assert set(graph.edges) == {("root", "child")}
    expected = {"root", "child", "unrelated"} if view == "hierarchy" else {
        "root", "child"
    }
    assert set(graph) == expected
    assert "entity" not in graph
    assert all(not data["parents"] and not data["children"]
               for data in engine.patterns.values())


def test_inheritance_depths_are_shortest_paths_and_cycles_stay_visible(
    drawn_graphs,
):
    engine = ATLASEngine()
    _add(engine, Pattern(pattern_id="root", parents=["child"]))
    _add(engine, Pattern(pattern_id="child", parents=["root"]))
    _add(engine, Pattern(pattern_id="grandchild", parents=["child"]))
    visualizer = PatternVisualizer(engine)

    _render(visualizer, "inheritance", max_depth=1)
    graph = drawn_graphs[-1]
    assert set(graph) == {"root", "child"}
    assert set(graph.edges) == {("root", "child"), ("child", "root")}
    assert nx.get_node_attributes(graph, "depth") == {"root": 0, "child": 1}

    _render(visualizer, "inheritance", max_depth=0)
    graph = drawn_graphs[-1]
    assert set(graph) == {"root"}
    assert not graph.edges
    assert nx.get_node_attributes(graph, "depth") == {"root": 0}

    _render(visualizer, "inheritance", max_depth=2)
    graph = drawn_graphs[-1]
    assert set(graph.edges) == {
        ("root", "child"), ("child", "root"), ("child", "grandchild")
    }
    assert nx.get_node_attributes(graph, "depth") == {
        "root": 0, "child": 1, "grandchild": 2
    }


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("visualize_pattern_hierarchy", {"layout": "spring"}),
        ("visualize_pattern_hierarchy", {"layout": "hierarchical"}),
        ("visualize_pattern_hierarchy", {"layout": "circular"}),
        ("visualize_pattern_inheritance_tree", {"root_pattern_id": "root"}),
        ("visualize_pattern_effectiveness", {}),
        ("visualize_pattern_similarity_matrix", {}),
        ("visualize_qkit_analysis", {}),
    ],
)
def test_complete_pattern_plotting_calls_preserve_global_numpy_state(
    method, kwargs
):
    engine = ATLASEngine()
    pattern_engine = PatternEngine()
    for pattern in (
        Pattern(pattern_id="root", children=["child"], qkit=["q1"]),
        Pattern(pattern_id="child", qkit=["q1", "q2"]),
    ):
        assert pattern.add_instance(f"instance-{pattern.id}")
        _add(engine, pattern)
        assert pattern_engine.add_pattern(pattern)
    visualizer = PatternVisualizer(engine, pattern_engine)
    before = np.random.get_state()
    comparison = np.random.RandomState()
    comparison.set_state(before)
    expected_draws = comparison.random_sample(5)
    figure = None
    try:
        figure = getattr(visualizer, method)(**kwargs)
        assert isinstance(figure, Figure)
        figure.canvas.draw()
        after = np.random.get_state()
        assert after[0] == before[0]
        np.testing.assert_array_equal(after[1], before[1])
        assert after[2:] == before[2:]
        np.testing.assert_array_equal(
            np.random.random_sample(5), expected_draws
        )
    finally:
        if figure is not None:
            plt.close(figure)
        np.random.set_state(before)
