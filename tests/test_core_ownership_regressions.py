"""Regression contracts for records, relationship occurrences and exports."""

import copy
import io
import json
from datetime import date, datetime

import networkx as nx
import pytest

from atlas.core.engine import ATLASEngine


@pytest.mark.parametrize('kind', ['entity', 'pattern', 'query'])
def test_replacement_discards_old_attributes_without_losing_edges(kind):
    atlas = ATLASEngine()
    add = getattr(atlas, f'add_{kind}')
    assert add('record', {'obsolete': True, 'name': 'old'})
    assert atlas.add_entity('peer', {})
    assert atlas.add_relationship('record', 'peer', 'related')
    assert add('record', {'name': 'new'})
    assert atlas.graph.nodes['record'] == {'name': 'new', 'node_type': kind}
    assert atlas.get_relationships('record') == [('peer', 'related')]


@pytest.mark.parametrize('first', ['parent', 'child'])
def test_hierarchy_insertion_order_and_unresolved_declarations(first):
    atlas = ATLASEngine()
    records = {'parent': {}, 'child': {'parents': ['parent', 'absent']}}
    second = 'child' if first == 'parent' else 'parent'
    assert atlas.add_pattern(first, records[first])
    assert set(atlas.graph) == {first}
    assert atlas.add_pattern(second, records[second])
    assert set(atlas.get_pattern_hierarchy_graph().edges) == {
        ('parent', 'child'),
    }
    assert 'absent' not in atlas.graph
    assert records['child']['parents'] == ['parent', 'absent']
    assert atlas.add_pattern('absent', {})
    assert set(atlas.get_pattern_hierarchy_graph().edges) == {
        ('parent', 'child'), ('absent', 'child'),
    }


def test_hierarchy_replacement_preserves_peer_and_explicit_ownership():
    atlas = ATLASEngine()
    atlas.add_pattern('parent', {'children': ['child']})
    atlas.add_pattern('child', {'parents': ['parent']})
    atlas.add_pattern('parent', {})
    assert atlas.graph.has_edge('parent', 'child')
    atlas.add_relationship('parent', 'child', 'parent_of')
    atlas.add_relationship('parent', 'child', 'annotates')
    atlas.add_pattern('child', {})
    edge = atlas.graph.edges['parent', 'child']
    assert edge['relationship_type'] == 'annotates'
    assert set(atlas.get_pattern_hierarchy_graph().edges) == {
        ('parent', 'child'),
    }
    assert atlas.patterns['parent'] == {}
    assert atlas.patterns['child'] == {}


def test_mutable_declarations_reconcile_without_mirroring_or_placeholders():
    atlas = ATLASEngine()
    atlas.add_pattern('parent', {})
    atlas.add_pattern('child', {'parents': ['parent']})
    atlas.patterns['child']['parents'].clear()
    atlas.get_metrics()
    assert not atlas.graph.has_edge('parent', 'child')
    atlas.patterns['parent']['children'] = ['child', 'missing']
    hierarchy = atlas.get_pattern_hierarchy_graph()
    assert set(hierarchy.edges) == {('parent', 'child')}
    hierarchy.remove_edge('parent', 'child')
    assert atlas.graph.has_edge('parent', 'child')
    assert atlas.patterns['child']['parents'] == []
    assert 'missing' not in atlas.graph


def test_relationship_occurrences_keep_repeats_and_legacy_edge_indexing():
    atlas = ATLASEngine()
    atlas.add_entity('a', {})
    atlas.add_entity('b', {})
    for kind in ('first', 'second', 'second'):
        assert atlas.add_relationship('a', 'b', kind)
    assert type(atlas.graph) is nx.DiGraph
    assert atlas.graph.edges['a', 'b']['relationship_type'] == 'second'
    expected = [('b', 'first'), ('b', 'second'), ('b', 'second')]
    assert atlas.get_relationships('a') == expected
    data = json.loads(atlas.export_graph('json'))
    edges = data.get('edges', data.get('links'))
    assert [r['relationship_type'] for r in edges[0]['relationships']] == [
        'first', 'second', 'second',
    ]
    for format_name, reader in [
        ('graphml', nx.read_graphml), ('gexf', nx.read_gexf),
    ]:
        restored = reader(io.BytesIO(atlas.export_graph(format_name).encode()))
        records = json.loads(restored.edges['a', 'b']['relationships'])
        assert [r['relationship_type'] for r in records] == [
            'first', 'second', 'second',
        ]


def test_owned_relationship_refresh_does_not_remove_identical_manual_calls():
    atlas = ATLASEngine()
    for name in ('a', 'b', 'c'):
        atlas.add_entity(name, {})
    atlas.add_relationship('a', 'b', 'references')
    assert atlas.replace_owned_relationships(
        'source', [('a', 'b', 'references')],
    )
    assert atlas.get_relationships('a').count(('b', 'references')) == 2
    assert not atlas.replace_owned_relationships(
        'source', [('a', 'missing', 'references')],
    )
    assert atlas.get_relationships('a').count(('b', 'references')) == 2
    assert atlas.replace_owned_relationships(
        'source', [('a', 'c', 'references')],
    )
    assert atlas.get_relationships('a') == [
        ('b', 'references'), ('c', 'references'),
    ]
    assert atlas.replace_owned_relationships('source', [])
    assert atlas.get_relationships('a') == [('b', 'references')]
    assert not atlas.graph.has_edge('a', 'c')


@pytest.mark.parametrize('formats', [
    ('graphml', 'json', 'gexf'), ('json', 'gexf', 'graphml'),
])
def test_export_is_detached_and_preserves_json_nulls(formats):
    atlas = ATLASEngine()
    record = {
        'missing': None, 'nested': {'values': [1, None, {'ok': True}]},
        'set': {'b', 'a'}, 'date': date(2024, 1, 2),
        'time': datetime(2024, 1, 2, 3, 4, 5),
    }
    atlas.add_entity('a', record)
    atlas.add_entity('b', {})
    atlas.add_relationship('a', 'b', 'related')
    nodes_before = copy.deepcopy(dict(atlas.graph.nodes(data=True)))
    edges_before = copy.deepcopy(list(atlas.graph.edges(data=True)))
    for format_name in formats:
        content = atlas.export_graph(format_name)
        assert content
        if format_name == 'json':
            node = next(
                n for n in json.loads(content)['nodes'] if n['id'] == 'a'
            )
            assert node['missing'] is None
            assert node['nested'] == record['nested']
            assert node['set'] == ['a', 'b']
            assert node['date'] == '2024-01-02'
        else:
            reader = (
                nx.read_graphml if format_name == 'graphml' else nx.read_gexf
            )
            node = reader(io.BytesIO(content.encode())).nodes['a']
            assert 'missing' not in node
            assert json.loads(node['nested']) == record['nested']
        assert dict(atlas.graph.nodes(data=True)) == nodes_before
        assert list(atlas.graph.edges(data=True)) == edges_before
        assert atlas.entities['a'] is record


def test_failed_xml_writer_does_not_sanitize_live_data(monkeypatch):
    atlas = ATLASEngine()
    record = {'nested': [None, {'value': 1}], 'missing': None}
    atlas.add_entity('a', record)

    def fail(graph):
        raise ValueError('writer refused')

    monkeypatch.setattr(nx, 'generate_graphml', fail)
    assert atlas.export_graph('graphml') == ''
    assert atlas.graph.nodes['a']['nested'] is record['nested']
    assert atlas.graph.nodes['a']['missing'] is None
    restored = json.loads(atlas.export_graph('json'))['nodes'][0]
    assert restored['nested'] == record['nested']


def test_xml_keeps_networkx_default_metadata_structured():
    atlas = ATLASEngine()
    atlas.add_entity('a', {'tier': 'custom'})
    atlas.graph.graph['node_default'] = {'tier': 'standard', 'absent': None}
    exported = atlas.export_graph('graphml')
    restored = nx.read_graphml(io.BytesIO(exported.encode()))
    assert restored.nodes['a']['tier'] == 'custom'
    assert restored.graph['node_default']['tier'] == 'standard'
    assert atlas.graph.graph['node_default'] == {
        'tier': 'standard', 'absent': None,
    }
