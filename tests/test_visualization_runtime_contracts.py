"""Runtime contracts for real Matplotlib charts, animations, and reports."""

from contextlib import contextmanager
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
from matplotlib.patches import Wedge
import numpy as np
from PIL import Image
import pytest

from atlas.core.engine import ATLASEngine
from atlas.entities.entity import Entity
from atlas.patterns.pattern import Pattern
from atlas.patterns.pattern_engine import PatternEngine
from atlas.visualization.animation_viz import AnimationVisualizer
from atlas.visualization.metrics_viz import MetricsVisualizer


@pytest.fixture(autouse=True)
def close_created_figures():
    existing = set(plt.get_fignums())
    yield
    for number in set(plt.get_fignums()) - existing:
        plt.close(number)


@pytest.fixture
def populated_engines():
    atlas = ATLASEngine()
    patterns = PatternEngine()
    parent = Pattern(pattern_id="parent", children=["child"], qkit=["q1"])
    child = Pattern(pattern_id="child", qkit=["q2", "q3"])
    # A parent-only declaration, with its endpoint registered later.
    for pattern in (parent, child):
        assert patterns.add_pattern(pattern)
        assert atlas.add_pattern(pattern.id, pattern.to_dict())
    for entity_id in ("first", "second"):
        entity = Entity(entity_id=entity_id, attributes={"name": entity_id})
        assert atlas.add_entity(entity.id, entity.to_dict())
    # A directed cycle keeps query simulation nonempty from any starting node.
    for source, target in (
        ("first", "parent"), ("child", "second"), ("second", "first")
    ):
        assert atlas.add_relationship(source, target, "related")
    return atlas, patterns


@contextmanager
def unchanged_numpy_random_state():
    """Check both the complete MT19937 state and subsequent public draws."""
    original = np.random.get_state()
    try:
        np.random.seed(1937)
        np.random.normal()  # Include a cached Gaussian in the state contract.
        before = np.random.get_state()
        yield
        after = np.random.get_state()
        assert after[0] == before[0]
        np.testing.assert_array_equal(after[1], before[1])
        assert after[2:] == before[2:]
        expected = np.random.RandomState()
        expected.set_state(before)
        np.testing.assert_array_equal(
            np.random.random_sample(10), expected.random_sample(10)
        )
    finally:
        np.random.set_state(original)


def assert_rendered_image(path, *, animated=False):
    """Decode the artifact and require visible, nonuniform rendered content."""
    with Image.open(path) as image:
        assert image.width > 0 and image.height > 0
        assert image.format == ("GIF" if animated else "PNG")
        frame_count = getattr(image, "n_frames", 1)
        assert frame_count >= 1
        for frame in range(frame_count):
            image.seek(frame)
            image.load()
            assert any(
                low < high for low, high in image.convert("RGB").getextrema()
            )
        return frame_count


def test_empty_overview_renders_explicit_no_data(tmp_path):
    path = tmp_path / "empty-overview.png"
    with unchanged_numpy_random_state():
        figure = MetricsVisualizer(ATLASEngine()).visualize_system_overview(
            figsize=(8, 6), save_path=str(path)
        )
        assert isinstance(figure, Figure)
        figure.canvas.draw()
        overview = figure.axes[0]
        assert any(
            "No component data" in text.get_text() for text in overview.texts
        )
        assert not any(isinstance(patch, Wedge) for patch in overview.patches)
        assert "Simulated" in figure.axes[3].get_title()
    assert_rendered_image(path)


def test_populated_overview_retains_real_distribution_and_simulation(
    populated_engines,
):
    atlas, _ = populated_engines
    with unchanged_numpy_random_state():
        figure = MetricsVisualizer(atlas).visualize_system_overview(
            figsize=(8, 6)
        )
        figure.canvas.draw()
        wedges = [
            patch for patch in figure.axes[0].patches
            if isinstance(patch, Wedge)
        ]
        assert len(wedges) == 4
        metrics = atlas.get_metrics()
        counts = np.array([
            metrics["entities_created"], metrics["patterns_created"],
            metrics["queries_executed"], metrics["relationships_added"],
        ])
        np.testing.assert_allclose(
            [wedge.theta2 - wedge.theta1 for wedge in wedges],
            counts / counts.sum() * 360,
            atol=0.0001,
        )
        rng = np.random.RandomState(42)
        for line, rate in zip(figure.axes[3].lines, (2, 1, 5)):
            values = line.get_ydata()
            np.testing.assert_array_equal(
                values, rng.poisson(rate, len(values))
            )


@pytest.mark.parametrize("method, arguments", [
    ("visualize_system_overview", {}),
    ("visualize_performance_metrics", {}),
    ("visualize_quality_metrics", {}),
    ("create_metrics_comparison", {"metrics_data": {
        "first": {"quality": 0.4, "confidence": 0.8},
        "second": {"quality": 0.9, "confidence": 0.6},
    }}),
])
def test_metrics_public_calls_preserve_global_rng(
    populated_engines, tmp_path, method, arguments
):
    atlas, _ = populated_engines
    visualizer = MetricsVisualizer(atlas)
    path = tmp_path / f"{method}.png"
    with unchanged_numpy_random_state():
        figure = getattr(visualizer, method)(
            **arguments, figsize=(8, 6), save_path=str(path)
        )
        assert isinstance(figure, Figure)
        figure.canvas.draw()
    assert_rendered_image(path)


def test_empty_default_report_contains_real_charts_and_json(tmp_path):
    base = tmp_path / "empty-report"
    with unchanged_numpy_random_state():
        report = MetricsVisualizer(ATLASEngine()).export_metrics_report(
            str(base)
        )
    assert report["summary"]["total_components"] == 0
    assert report["summary"]["network_density"] == 0
    assert report["system_metrics"]["total_nodes"] == 0
    expected_paths = [
        f"{base}_{kind}.png" for kind in ("overview", "performance", "quality")
    ]
    assert report["charts_generated"] == expected_paths
    for path in report["charts_generated"]:
        assert_rendered_image(path)
    saved = json.loads(Path(f"{base}_report.json").read_text())
    assert saved == report


@pytest.mark.parametrize("method, arguments", [
    ("animate_network_growth", {"time_steps": 3}),
    ("animate_pattern_discovery", {"time_steps": 3}),
    ("animate_query_execution", {"query_steps": 4}),
    ("animate_system_metrics", {"time_steps": 3}),
])
def test_complete_animation_calls_preserve_global_rng(
    populated_engines, tmp_path, method, arguments
):
    atlas, patterns = populated_engines
    visualizer = AnimationVisualizer(atlas, patterns)
    visualizer.dpi = 40
    path = tmp_path / f"{method}.gif"
    with unchanged_numpy_random_state():
        result = getattr(visualizer, method)(
            **arguments, figsize=(6, 4), save_path=str(path)
        )
        assert isinstance(result, FuncAnimation)
        # Saving traverses all frames, including layouts inside callbacks.
        result._fig.canvas.draw()
    assert assert_rendered_image(path, animated=True) >= 2


def test_timeline_public_call_preserves_global_rng(tmp_path):
    path = tmp_path / "timeline.png"
    with unchanged_numpy_random_state():
        figure = AnimationVisualizer().create_interactive_timeline(
            time_window_days=7, figsize=(8, 6), save_path=str(path)
        )
        figure.canvas.draw()
        assert "Simulated" in figure._suptitle.get_text()
    assert_rendered_image(path)


def test_comprehensive_animation_suite_preserves_global_rng(
    populated_engines, tmp_path
):
    atlas, patterns = populated_engines
    visualizer = AnimationVisualizer(atlas, patterns)
    visualizer.dpi = 25
    with unchanged_numpy_random_state():
        result = visualizer.create_comprehensive_animation_suite(
            str(tmp_path), "contracts"
        )
    assert result["failed_animations"] == []
    assert {item["name"] for item in result["created_animations"]} == {
        "network_growth", "pattern_discovery", "query_execution",
        "system_metrics", "interactive_timeline",
    }
    assert result["total_size_mb"] > 0
    for item in result["created_animations"]:
        path = Path(item["file_path"])
        assert path.parent == tmp_path
        assert_rendered_image(path, animated=path.suffix == ".gif")
    saved = json.loads((tmp_path / "contracts_summary.json").read_text())
    assert saved == result


@pytest.mark.parametrize("nodes, edges, steps, frame, expected_density", [
    (["a", "b"], [("a", "b"), ("b", "a")], 1, 0, 1.0),
    (["a", "b"], [("a", "b")], 1, 0, 0.5),
    (["a"], [], 1, 0, 0.0),
    (["a", "b"], [("a", "b")], 4, 0, 0.0),
])
def test_network_density_uses_the_directed_frame_graph(
    tmp_path, nodes, edges, steps, frame, expected_density
):
    atlas = ATLASEngine()
    for node in nodes:
        assert atlas.add_entity(node, {"id": node})
    for source, target in edges:
        assert atlas.add_relationship(source, target, "related")
    visualizer = AnimationVisualizer(atlas)
    visualizer.dpi = 40
    path = tmp_path / "density.gif"
    with unchanged_numpy_random_state():
        result = visualizer.animate_network_growth(
            time_steps=steps, figsize=(6, 4), save_path=str(path)
        )
        assert isinstance(result, FuncAnimation)
        # Inspect the real callback for an empty intermediate frame as well.
        result._func(frame)
        density_text = [
            text.get_text() for text in result._fig.axes[0].texts
            if text.get_text().startswith("Density:")
        ]
        assert density_text == [f"Density: {expected_density:.3f}"]
    assert_rendered_image(path, animated=True)


def test_empty_network_retains_its_no_animation_contract():
    with unchanged_numpy_random_state():
        result = AnimationVisualizer(ATLASEngine()).animate_network_growth()
        assert result is None
        figure = plt.gcf()
        figure.canvas.draw()
        assert any(
            "No nodes to animate" in text.get_text()
            for text in figure.axes[0].texts
        )


def test_simulated_metrics_retain_seeded_data_and_heuristics(
    populated_engines, tmp_path
):
    atlas, patterns = populated_engines
    visualizer = AnimationVisualizer(atlas, patterns)
    visualizer.dpi = 40
    metrics = atlas.get_metrics()
    steps = 3
    rng = np.random.RandomState(42)
    entities = [
        metrics["entities_created"] + int(i * 2 + rng.poisson(1))
        for i in range(steps)
    ]
    pattern_counts = [
        metrics["patterns_created"] + int(i * 0.5 + rng.poisson(0.3))
        for i in range(steps)
    ]
    relationships = [
        metrics["relationships_added"] + int(i * 3 + rng.poisson(2))
        for i in range(steps)
    ]
    with unchanged_numpy_random_state():
        result = visualizer.animate_system_metrics(
            time_steps=steps, figsize=(8, 6),
            save_path=str(tmp_path / "metrics.gif")
        )
        assert isinstance(result, FuncAnimation)
        axes = result._fig.axes
        for line, expected in zip(
            axes[0].lines, (entities, pattern_counts, relationships)
        ):
            np.testing.assert_array_equal(line.get_ydata(), expected)
        np.testing.assert_allclose(axes[1].lines[0].get_ydata(), [
            min(1.0, count / max(1, size * (size - 1) / 2))
            for size, count in zip(entities, relationships)
        ])
        np.testing.assert_allclose(axes[2].lines[0].get_ydata(), [
            count / max(1, size)
            for size, count in zip(entities, pattern_counts)
        ])
        assert "Simulated" in result._fig._suptitle.get_text()


def test_discovery_animation_uses_effective_mutable_hierarchy(
    populated_engines, tmp_path
):
    atlas, patterns = populated_engines
    # The late child is owned only by its parent's children declaration.
    assert atlas.patterns["child"]["parents"] == []
    visualizer = AnimationVisualizer(atlas, patterns)
    visualizer.dpi = 40
    with unchanged_numpy_random_state():
        first = visualizer.animate_pattern_discovery(
            time_steps=1, figsize=(6, 4),
            save_path=str(tmp_path / "declared.gif")
        )
        assert isinstance(first, FuncAnimation)
        assert len(first._fig.axes[0].patches) == 1

        # Direct edits are reconciled, and explicit relationships survive them.
        atlas.patterns["parent"]["children"].clear()
        second = visualizer.animate_pattern_discovery(
            time_steps=1, figsize=(6, 4),
            save_path=str(tmp_path / "withdrawn.gif")
        )
        assert isinstance(second, FuncAnimation)
        assert len(second._fig.axes[0].patches) == 0
        assert atlas.add_relationship("child", "parent", "parent_of")
        third = visualizer.animate_pattern_discovery(
            time_steps=1, figsize=(6, 4),
            save_path=str(tmp_path / "explicit.gif")
        )
        assert isinstance(third, FuncAnimation)
        assert len(third._fig.axes[0].patches) == 1
    assert atlas.patterns["parent"]["children"] == []
    assert atlas.patterns["child"]["parents"] == []
