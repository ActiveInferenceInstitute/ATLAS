"""Current-state contracts for independent pattern management and analysis."""

from copy import deepcopy

import pytest

from atlas.patterns.pattern import Pattern
from atlas.patterns.pattern_engine import PatternEngine


def _engine(*patterns):
    engine = PatternEngine()
    for pattern in patterns:
        assert engine.add_pattern(pattern)
    return engine


@pytest.mark.parametrize("declaration", ["parents", "children"])
@pytest.mark.parametrize("child_first", [False, True])
def test_late_endpoints_resolve_without_mirroring(declaration, child_first):
    parent = Pattern(pattern_id="parent")
    child = Pattern(pattern_id="child")
    if declaration == "parents":
        child.parents.append(parent.id)
    else:
        parent.children.append(child.id)
    authored = deepcopy((parent.parents, parent.children,
                         child.parents, child.children))
    first, second = (child, parent) if child_first else (parent, child)
    engine = _engine(first)

    assert set(engine.pattern_graph) == {first.id}
    assert not engine.pattern_graph.edges
    assert engine.add_pattern(second)
    assert set(engine.pattern_graph.edges) == {("parent", "child")}
    assert engine.get_pattern_hierarchy("child") == {
        "ancestors": {"parent"}, "descendants": set()
    }
    assert engine.get_pattern_hierarchy("parent") == {
        "ancestors": set(), "descendants": {"child"}
    }
    assert (parent.parents, parent.children,
            child.parents, child.children) == authored


def test_replacement_withdraws_only_replaced_owners_declarations():
    parent = Pattern(pattern_id="parent", children=["child"])
    peer = Pattern(pattern_id="peer", children=["child"])
    child = Pattern(pattern_id="child", parents=["parent"])
    other = Pattern(pattern_id="other")
    engine = _engine(parent, peer, child, other)
    graph = engine.pattern_graph

    replacement = Pattern(pattern_id="child", parents=["other"])
    assert engine.add_pattern(replacement)
    assert engine.patterns["child"] is replacement
    assert graph.nodes["child"]["pattern"] is replacement
    assert set(graph.edges) == {
        ("parent", "child"), ("peer", "child"), ("other", "child")
    }
    assert replacement.parents == ["other"]
    assert replacement.children == []
    assert other.children == []

    assert engine.add_pattern(Pattern(pattern_id="parent"))
    assert set(graph.edges) == {("peer", "child"), ("other", "child")}
    assert engine.add_pattern(Pattern(pattern_id="child"))
    assert set(graph.edges) == {("peer", "child")}
    assert engine.pattern_graph is graph


def test_removed_endpoint_reactivates_only_surviving_declarations():
    parent = Pattern(pattern_id="parent", children=["child", "missing"])
    child = Pattern(pattern_id="child", children=["grandchild"])
    engine = _engine(parent, child, Pattern(pattern_id="grandchild"))

    assert engine.remove_pattern("child")
    assert parent.children == ["child", "missing"]
    assert set(engine.pattern_graph) == {"parent", "grandchild"}
    assert not engine.pattern_graph.edges
    assert engine.add_pattern(Pattern(pattern_id="child"))
    assert set(engine.pattern_graph.edges) == {("parent", "child")}
    assert "missing" not in engine.pattern_graph
    assert engine.add_pattern(Pattern(pattern_id="missing"))
    assert set(engine.pattern_graph.edges) == {
        ("parent", "child"), ("parent", "missing")
    }


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("get_pattern_hierarchy_graph", ()),
        ("get_pattern_hierarchy", ("child",)),
        ("calculate_pattern_similarity", ("parent", "child")),
        ("find_similar_patterns", ("child",)),
        ("detect_pattern_clusters", ()),
        ("suggest_pattern_merges", ()),
        ("analyze_pattern_usage", ()),
        ("optimize_pattern_hierarchy", ()),
        ("get_statistics", ()),
    ],
)
def test_analysis_boundaries_reconcile_direct_list_edits(method, args):
    parent = Pattern(pattern_id="parent")
    child = Pattern(pattern_id="child")
    engine = _engine(parent, child)
    graph = engine.pattern_graph

    parent.children.append("child")
    getattr(engine, method)(*args)
    assert set(graph.edges) == {("parent", "child")}
    assert child.parents == []

    parent.children.clear()
    child.parents.append("missing")
    getattr(engine, method)(*args)
    assert not graph.edges
    assert set(graph) == {"parent", "child"}
    assert child.parents == ["missing"]
    assert engine.pattern_graph is graph


def test_hierarchy_results_do_not_expose_mutable_cached_topology():
    parent = Pattern(pattern_id="parent", children=["child"])
    engine = _engine(parent, Pattern(pattern_id="child"))
    engine.get_pattern_hierarchy("child")["ancestors"].clear()
    snapshot = engine.get_pattern_hierarchy_graph()
    snapshot.remove_node("parent")

    assert engine.get_pattern_hierarchy("child")["ancestors"] == {"parent"}
    assert set(engine.pattern_graph.edges) == {("parent", "child")}
    assert engine.pattern_graph.nodes["parent"]["pattern"] is parent


@pytest.mark.parametrize("declaration", ["parents", "children"])
def test_hierarchy_roles_use_effective_degrees(declaration):
    parent = Pattern(pattern_id="parent")
    child = Pattern(pattern_id="child")
    if declaration == "parents":
        child.parents.append("parent")
    else:
        parent.children.append("child")
    unresolved = Pattern(pattern_id="unresolved", parents=["missing"])
    engine = _engine(child, parent, unresolved)

    analysis = engine.analyze_pattern_usage()
    assert set(analysis["root_patterns"]) == {"parent", "unresolved"}
    assert set(analysis["leaf_patterns"]) == {"child", "unresolved"}
    assert analysis["orphaned_patterns"] == ["unresolved"]
    assert analysis["hierarchy_depth"] == 1
    assert engine.get_statistics()["graph_edges"] == 1


def test_mutable_similarity_inputs_keep_original_weights():
    left = Pattern(pattern_id="left", qkit=["q"], attributes={"key": 1})
    right = Pattern(pattern_id="right", qkit=["q"], attributes={"key": 2})
    engine = _engine(left, right)
    assert engine.calculate_pattern_similarity("left", "right") == 1.0

    right.qkit.append("extra")
    assert engine.calculate_pattern_similarity("right", "left") == 0.75
    assert right.remove_qkit_item("q")
    assert engine.calculate_pattern_similarity("left", "right") == 0.5
    right.qkit[:] = ["q"]
    right.attributes.clear()
    assert engine.calculate_pattern_similarity("left", "right") == 0.7
    right.attributes["key"] = {"nested": "different value"}
    assert engine.calculate_pattern_similarity("left", "right") == 1.0


def test_clustering_and_merge_suggestions_follow_direct_mutations():
    left = Pattern(pattern_id="left", qkit=["q"], attributes={"key": 1})
    right = Pattern(pattern_id="right", qkit=["q"], attributes={"key": 2})
    engine = _engine(left, right)

    assert list(engine.detect_pattern_clusters(0.8).values()) == [
        {"left", "right"}
    ]
    assert len(engine.suggest_pattern_merges(0.8)) == 1
    right.qkit[:] = ["other"]
    right.attributes.clear()
    right.attributes["other"] = True

    assert engine.calculate_pattern_similarity("left", "right") == 0.2
    assert {frozenset(group) for group in
            engine.detect_pattern_clusters(0.8).values()} == {
        frozenset({"left"}), frozenset({"right"})
    }
    assert engine.find_similar_patterns("left", 0.8) == []
    assert engine.suggest_pattern_merges(0.8) == []

    assert engine.add_pattern(Pattern(
        pattern_id="right", qkit=["q"], attributes={"key": 3}
    ))
    suggestion, = engine.suggest_pattern_merges(0.8)
    assert suggestion["similarity"] == 1.0
    assert suggestion["common_qkit"] == ["q"]
    assert suggestion["common_attributes"] == ["key"]


def test_similarity_revalidates_mutable_hierarchy_inputs():
    parent = Pattern(pattern_id="parent")
    left = Pattern(pattern_id="left")
    right = Pattern(pattern_id="right")
    engine = _engine(parent, left, right)
    assert engine.calculate_pattern_similarity("left", "right") == 1.0

    parent.children.append("left")
    assert engine.calculate_pattern_similarity("left", "right") == 0.8
    right.parents.append("parent")
    assert engine.calculate_pattern_similarity("left", "right") == 1.0
    parent.children.clear()
    assert engine.calculate_pattern_similarity("left", "right") == 0.8


@pytest.mark.parametrize(
    ("children", "redundant", "cycles"),
    [
        ({"a": ["b"], "b": []}, set(), set()),
        ({"a": ["b", "c"], "b": ["c"], "c": []},
         {("a", "c")}, set()),
        ({"a": ["b"], "b": ["c"], "c": ["a"]},
         set(), {frozenset({"a", "b", "c"})}),
        ({"a": ["a"]}, set(), {frozenset({"a"})}),
        ({"a": ["a", "b"], "b": ["a"]},
         {("a", "a")}, {frozenset({"a"}), frozenset({"a", "b"})}),
    ],
)
def test_redundancy_requires_an_alternate_path_and_retains_cycles(
    children, redundant, cycles
):
    engine = _engine(*[
        Pattern(pattern_id=pattern_id, children=list(child_ids))
        for pattern_id, child_ids in children.items()
    ])
    graph = engine.pattern_graph
    before_edges = list(graph.edges(data=True))
    before_lists = deepcopy({pid: p.children for pid, p in
                             engine.patterns.items()})

    suggestions = engine.optimize_pattern_hierarchy()
    assert {
        (item["parent"], item["pattern"]) for item in suggestions
        if item["type"] == "redundant_relationship"
    } == redundant
    assert {
        frozenset(item["patterns"]) for item in suggestions
        if item["type"] == "cycle_detected"
    } == cycles
    assert list(graph.edges(data=True)) == before_edges
    assert (
        {pid: p.children for pid, p in engine.patterns.items()} == before_lists
    )


def test_cycles_do_not_hide_hierarchy_roles():
    engine = _engine(
        Pattern(pattern_id="a", children=["b"]),
        Pattern(pattern_id="b", children=["a"]),
        Pattern(pattern_id="isolated"),
    )
    analysis = engine.analyze_pattern_usage()
    assert analysis["root_patterns"] == ["isolated"]
    assert analysis["leaf_patterns"] == ["isolated"]
    assert analysis["orphaned_patterns"] == ["isolated"]
    assert analysis["hierarchy_depth"] is None


def test_effectiveness_refreshes_after_usage_and_derivation_changes():
    pattern = Pattern(pattern_id="pattern")
    assert pattern.effectiveness_score == 0.0
    assert pattern.add_instance("entity")
    assert pattern.effectiveness_score == pytest.approx(0.03)
    assert pattern.add_derivation("derived")
    assert pattern.effectiveness_score == pytest.approx(0.13)
    assert pattern.remove_instance("entity")
    assert pattern.effectiveness_score == pytest.approx(0.1)

    pattern.derivations.clear()
    assert pattern.get_statistics()["effectiveness_score"] == 0.0
    assert pattern.effectiveness_score == 0.0
    pattern.effectiveness_score = 0.9
    data = pattern.to_dict()
    assert data["effectiveness_score"] == 0.0
    assert data["statistics"]["effectiveness_score"] == 0.0
    assert pattern.effectiveness_score == 0.0


@pytest.mark.parametrize(
    ("usage", "instances", "derivations", "expected"),
    [(0, 0, 0, 0.0), (1, 1, 0, 0.03), (0, 1, 1, 0.12),
     (250, 70, 20, 1.0)],
)
def test_direct_usage_mutations_preserve_effectiveness_formula(
    usage, instances, derivations, expected
):
    pattern = Pattern(pattern_id="pattern")
    pattern.calculate_effectiveness_score()
    pattern.usage_count = usage
    pattern.instances.update(f"entity-{i}" for i in range(instances))
    pattern.derivations.update(f"derived-{i}" for i in range(derivations))

    statistics = pattern.get_statistics()
    data = pattern.to_dict()
    assert statistics["effectiveness_score"] == pytest.approx(expected)
    assert data["effectiveness_score"] == pytest.approx(expected)
    assert data["statistics"]["effectiveness_score"] == pytest.approx(expected)
    assert pattern.effectiveness_score == pytest.approx(expected)


def test_serialization_calculates_one_current_effectiveness_value():
    class CountingPattern(Pattern):
        calculations = 0

        def calculate_effectiveness_score(self):
            self.calculations += 1
            return super().calculate_effectiveness_score()

    pattern = CountingPattern(pattern_id="pattern")
    pattern.instances.add("entity")
    pattern.usage_count = 1
    data = pattern.to_dict()

    assert pattern.calculations == 1
    assert data["effectiveness_score"] == pytest.approx(0.03)
    assert data["statistics"]["effectiveness_score"] == (
        data["effectiveness_score"]
    )


def test_restoration_recomputes_instead_of_trusting_a_saved_score():
    pattern = Pattern(pattern_id="pattern", parents=["unresolved"])
    assert pattern.add_instance("entity")
    data = pattern.to_dict()
    data["effectiveness_score"] = 0.99
    data["statistics"]["effectiveness_score"] = 0.99

    restored = Pattern.from_dict(data)
    assert restored.effectiveness_score == pytest.approx(0.03)
    assert restored.parents == ["unresolved"]
    restored_data = restored.to_dict()
    assert restored_data["effectiveness_score"] == pytest.approx(0.03)
    assert restored_data["statistics"]["effectiveness_score"] == pytest.approx(
        0.03
    )


def test_replacing_unresolved_declarations_does_not_resurrect_them():
    engine = _engine(
        Pattern(pattern_id="parent", children=["withdrawn"]),
        Pattern(pattern_id="peer", children=["withdrawn"]),
    )
    assert engine.add_pattern(
        Pattern(pattern_id="parent", children=["current"])
    )
    assert set(engine.pattern_graph) == {"parent", "peer"}
    assert engine.add_pattern(Pattern(pattern_id="withdrawn"))
    assert engine.add_pattern(Pattern(pattern_id="current"))

    assert set(engine.pattern_graph.edges) == {
        ("peer", "withdrawn"), ("parent", "current")
    }
    assert engine.patterns["parent"].children == ["current"]
    assert engine.patterns["peer"].children == ["withdrawn"]


def test_removing_last_instance_refreshes_every_effectiveness_read():
    pattern = Pattern(pattern_id="pattern")
    assert pattern.add_instance("entity")
    assert pattern.to_dict()["effectiveness_score"] == pytest.approx(0.03)
    assert pattern.remove_instance("entity")

    assert pattern.effectiveness_score == 0.0
    assert pattern.get_statistics()["effectiveness_score"] == 0.0
    data = pattern.to_dict()
    assert data["effectiveness_score"] == 0.0
    assert data["statistics"]["effectiveness_score"] == 0.0

    pattern.instances.add("direct")
    pattern.usage_count = 1
    assert pattern.get_statistics()["effectiveness_score"] == pytest.approx(
        0.03
    )
    pattern.instances.clear()
    pattern.usage_count = 0
    data = pattern.to_dict()
    assert data["effectiveness_score"] == 0.0
    assert data["statistics"]["effectiveness_score"] == 0.0


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("calculate_pattern_similarity", ("only", "only")),
        ("find_similar_patterns", ("only",)),
        ("detect_pattern_clusters", ()),
        ("suggest_pattern_merges", ()),
    ],
)
def test_single_pattern_analysis_still_reconciles_mutable_topology(
    method, args
):
    pattern = Pattern(pattern_id="only")
    engine = _engine(pattern)
    pattern.children.append("only")
    getattr(engine, method)(*args)
    assert set(engine.pattern_graph.edges) == {("only", "only")}

    pattern.children.clear()
    getattr(engine, method)(*args)
    assert not engine.pattern_graph.edges
