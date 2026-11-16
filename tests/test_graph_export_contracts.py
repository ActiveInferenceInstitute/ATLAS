"""Exercise real exporter outputs, lossless labels and failure maps."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest

from atlas.core.engine import ATLASEngine
from atlas.visualization.graph_viz import GraphVisualizer


def populated_engine():
    atlas = ATLASEngine()
    atlas.add_entity('a', {'attributes': {'values': [1, None]}, 'empty': None})
    atlas.add_entity('b', {})
    for kind in ('references', 'uses', 'uses'):
        atlas.add_relationship('a', 'b', kind)
    return atlas


def test_graph_export_writes_readable_outputs_without_mutation(tmp_path):
    atlas = populated_engine()
    expected = json.loads(atlas.export_graph('json'))
    paths = GraphVisualizer(atlas).export_graph_formats(
        str(tmp_path / 'graph'),
    )
    assert set(paths) == {'graphml', 'gexf', 'edgelist', 'adjlist'}
    for name, reader in [('graphml', nx.read_graphml), ('gexf', nx.read_gexf)]:
        graph = reader(paths[name])
        assert set(graph) == {'a', 'b'}
        assert json.loads(graph.nodes['a']['attributes']) == {
            'values': [1, None],
        }
        assert [r['relationship_type'] for r in json.loads(
            graph.edges['a', 'b']['relationships']
        )] == ['references', 'uses', 'uses']
    edge_graph = nx.read_edgelist(paths['edgelist'], create_using=nx.DiGraph)
    assert len(edge_graph.edges['a', 'b']['relationships']) == 3
    adjacency = nx.read_adjlist(paths['adjlist'], create_using=nx.DiGraph)
    assert set(adjacency.edges) == {('a', 'b')}
    assert json.loads(atlas.export_graph('json')) == expected


def test_export_returns_only_successful_paths_on_partial_failure(tmp_path):
    base = tmp_path / 'graph'
    Path(f'{base}.gexf').mkdir()
    paths = GraphVisualizer(populated_engine()).export_graph_formats(str(base))
    assert set(paths) == {'graphml', 'edgelist', 'adjlist'}
    assert nx.read_graphml(paths['graphml']).has_edge('a', 'b')
    assert Path(f'{base}.gexf').is_dir()


def test_export_refusal_is_empty_mapping_not_success(tmp_path):
    base = tmp_path / 'missing' / 'graph'
    paths = GraphVisualizer(populated_engine()).export_graph_formats(str(base))
    assert paths == {}


def test_interactive_relationship_labels_include_every_occurrence():
    figure = GraphVisualizer(populated_engine()).create_interactive_network()
    assert figure.data[0].text[0] == 'a → b (references, uses, uses)'
    assert figure.data[0].hoverinfo == 'text'


def test_interactive_label_keeps_legacy_nonstring_relationship_display():
    atlas = populated_engine()
    assert atlas.add_relationship('a', 'b', 7)
    figure = GraphVisualizer(atlas).create_interactive_network()
    assert figure.data[0].text[0] == 'a → b (references, uses, uses, 7)'


@pytest.mark.parametrize('method,kwargs', [
    ('visualize_network_topology', {'layout': 'spring'}),
    ('visualize_network_topology', {'layout': 'random'}),
    ('visualize_entity_relationships', {'entity_id': 'a', 'layout': 'spring'}),
    ('visualize_entity_relationships', {'entity_id': 'a', 'layout': 'random'}),
    ('create_interactive_network', {}),
])
def test_graph_plotting_preserves_global_numpy_randomness(method, kwargs):
    visualizer = GraphVisualizer(populated_engine())
    before = np.random.get_state()
    try:
        figure = getattr(visualizer, method)(**kwargs)
        if isinstance(figure, plt.Figure):
            figure.canvas.draw()
            plt.close(figure)
        after = np.random.get_state()
        assert before[0] == after[0]
        assert np.array_equal(before[1], after[1])
        assert before[2:] == after[2:]
    finally:
        np.random.set_state(before)
