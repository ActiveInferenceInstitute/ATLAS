"""Regression contracts for query indexing, lifecycle and current scores."""

from datetime import datetime, timedelta
import json

import pytest

from atlas.queries.iquery import QueryStatus, iQuery


@pytest.fixture
def query_clock(monkeypatch):
    class QueryClock(datetime):
        current = datetime(2025, 1, 1, 12, 0, 0)

        @classmethod
        def now(cls):
            return cls.current

    monkeypatch.setattr("atlas.queries.iquery.datetime", QueryClock)
    return QueryClock


def assert_current_scores(query, quality, confidence):
    # Check exposed fields before any read method can refresh them.
    assert query.quality_score == pytest.approx(quality)
    assert query.confidence_score == pytest.approx(confidence)
    assert query.calculate_quality_score() == pytest.approx(quality)
    assert query.calculate_confidence_score() == pytest.approx(confidence)
    statistics = query.get_statistics()
    payload = query.to_dict()
    assert payload["statistics"] == statistics
    assert statistics["quality_score"] == pytest.approx(quality)
    assert statistics["confidence_score"] == pytest.approx(confidence)
    assert statistics["result_count"] == len(query.results)
    assert statistics["response_entity_count"] == len(query.response_entities)
    assert statistics["derived_pattern_count"] == len(query.derived_patterns)
    assert set(payload["response_entities"]) == query.response_entities
    assert set(payload["derived_patterns"]) == query.derived_patterns


def test_bulk_and_incremental_ingestion_have_identical_state(query_clock):
    incremental = iQuery(query_id="incremental")
    bulk = iQuery(query_id="bulk")
    seed = {"entity_id": "seed", "derived_patterns": ["seed-pattern"]}
    results = [
        {"entity_id": "one", "derived_patterns": ["p1", "p1"]},
        {"entity_id": "one", "derived_patterns": ["p2"]},
        {"entity_id": "two"},
        {"note": "A result without index fields"},
    ]
    for query in (incremental, bulk):
        assert query.start_execution() is True
        assert query.add_result(seed) is True
        query.get_statistics()

    for result in results:
        assert incremental.add_result(result) is True
    query_clock.current += timedelta(seconds=2)
    assert incremental.complete_execution() is True
    assert bulk.complete_execution(results) is True

    for query in (incremental, bulk):
        assert query.status is QueryStatus.COMPLETED
        assert query.results == [seed, *results]
        assert query.results[0] is seed
        assert query.results[1] is results[0]
        assert query.response_entities == {"seed", "one", "two"}
        assert query.derived_patterns == {"seed-pattern", "p1", "p2"}
        assert query.execution_time == 2.0
        assert_current_scores(query, 1.0, 1.0)
    assert incremental.get_statistics() == bulk.get_statistics()


def test_appending_after_scoring_updates_exposed_scores_and_indexes():
    query = iQuery()
    assert query.add_result({"entity_id": "one"}) is True
    assert_current_scores(query, 0.3, 0.6)

    assert query.add_result({
        "entity_id": "two", "derived_patterns": ["pattern"]
    }) is True
    assert query.response_entities == {"one", "two"}
    assert query.derived_patterns == {"pattern"}
    assert_current_scores(query, 0.7, 1.0)


def test_clear_resets_scores_and_indexes_without_replacing_mutable_objects():
    query = iQuery()
    results = query.results
    response_entities = query.response_entities
    derived_patterns = query.derived_patterns
    query.execution_time = 2.0
    assert query.add_result({
        "entity_id": "one", "derived_patterns": ["pattern"]
    }) is True
    assert_current_scores(query, 0.6, 0.8)

    query.clear_results()
    assert query.results is results
    assert query.response_entities is response_entities
    assert query.derived_patterns is derived_patterns
    assert results == []
    assert response_entities == set()
    assert derived_patterns == set()
    assert_current_scores(query, 0.0, 0.0)
    assert query.to_dict()["response_entities"] == []
    assert query.to_dict()["derived_patterns"] == []
    restored = iQuery.from_dict(json.loads(json.dumps(query.to_dict())))
    assert_current_scores(restored, 0.0, 0.0)
    assert restored.response_entities == set()
    assert restored.derived_patterns == set()


@pytest.mark.parametrize(
    ("method", "arguments", "status"),
    [
        ("complete_execution", (), QueryStatus.COMPLETED),
        ("fail_execution", ("execution failed",), QueryStatus.FAILED),
        ("cancel_execution", (), QueryStatus.CANCELLED),
    ],
)
@pytest.mark.parametrize(
    ("elapsed", "quality"), [(0, 0.3), (2, 0.4), (5, 0.3), (6, 0.3)]
)
def test_terminal_transitions_recompute_scores_using_final_execution_time(
    query_clock, method, arguments, status, elapsed, quality
):
    query = iQuery()
    assert query.start_execution() is True
    assert query.add_result({"entity_id": "one"}) is True
    assert_current_scores(query, 0.3, 0.6)
    if elapsed >= 5:
        # A scored public timing value must not survive finalization.
        query.execution_time = 1.0
        query.calculate_quality_score()
        assert_current_scores(query, 0.4, 0.6)

    query_clock.current += timedelta(seconds=elapsed)
    assert getattr(query, method)(*arguments) is True
    assert query.status is status
    assert query.completed_at == query_clock.current
    assert query.execution_time == float(elapsed)
    assert_current_scores(query, quality, 0.6)
    if status is QueryStatus.FAILED:
        assert query.error_message == "execution failed"


@pytest.mark.parametrize("method", ["fail_execution", "cancel_execution"])
def test_unstarted_terminal_queries_keep_empty_scores_and_no_duration(method):
    query = iQuery()
    arguments = ("failed before start",) if method == "fail_execution" else ()
    assert getattr(query, method)(*arguments) is True
    assert query.started_at is None
    assert query.completed_at is not None
    assert query.execution_time is None
    assert_current_scores(query, 0.0, 0.0)


@pytest.mark.parametrize(
    "boundary",
    [
        "calculate_quality_score",
        "calculate_confidence_score",
        "get_statistics",
        "to_dict",
    ],
)
@pytest.mark.parametrize("mutation", ["append", "nested", "replace", "clear"])
def test_analysis_boundaries_reconcile_direct_mutable_results(
    boundary, mutation
):
    query = iQuery()
    result = {"entity_id": "old", "derived_patterns": ["old-pattern"]}
    assert query.add_result(result) is True
    assert_current_scores(query, 0.5, 0.8)
    response_entities = query.response_entities
    derived_patterns = query.derived_patterns

    if mutation == "append":
        query.results.append({"entity_id": "new"})
        expected_entities = {"old", "new"}
        expected_patterns = {"old-pattern"}
        expected_scores = (0.7, 1.0)
    elif mutation == "nested":
        result["entity_id"] = "new"
        result["derived_patterns"][:] = []
        expected_entities = {"new"}
        expected_patterns = set()
        expected_scores = (0.3, 0.6)
    elif mutation == "replace":
        query.results[:] = [{"derived_patterns": ["new-pattern"]}]
        expected_entities = set()
        expected_patterns = {"new-pattern"}
        expected_scores = (0.3, 0.8)
    else:
        query.results.clear()
        expected_entities = set()
        expected_patterns = set()
        expected_scores = (0.0, 0.0)

    snapshot = getattr(query, boundary)()
    assert query.response_entities is response_entities
    assert query.derived_patterns is derived_patterns
    assert response_entities == expected_entities
    assert derived_patterns == expected_patterns
    if boundary == "to_dict":
        assert set(snapshot["response_entities"]) == expected_entities
        assert set(snapshot["derived_patterns"]) == expected_patterns
        assert snapshot["statistics"]["quality_score"] == pytest.approx(
            expected_scores[0]
        )
    if boundary == "get_statistics":
        assert snapshot["response_entity_count"] == len(expected_entities)
        assert snapshot["derived_pattern_count"] == len(expected_patterns)
    assert_current_scores(query, *expected_scores)


@pytest.mark.parametrize("empty_results", [False, True])
def test_restoration_rebuilds_legacy_stale_indexes_and_scores(
    query_clock, empty_results
):
    query = iQuery(query_id="persisted", context={"key": "value"})
    assert query.start_execution() is True
    query_clock.current += timedelta(seconds=2)
    assert query.complete_execution([
        {"entity_id": "one", "derived_patterns": ["pattern"]},
        {"entity_id": "two"},
    ]) is True
    payload = json.loads(json.dumps(query.to_dict()))
    payload["response_entities"] = ["obsolete"]
    payload["derived_patterns"] = ["obsolete-pattern"]
    payload["statistics"]["quality_score"] = 0.99
    payload["statistics"]["confidence_score"] = 0.99
    if empty_results:
        payload["results"] = []

    restored = iQuery.from_dict(payload)
    assert restored.id == query.id
    assert restored.ref_id == query.ref_id
    assert restored.context == query.context
    assert restored.status is QueryStatus.COMPLETED
    assert restored.created_at == query.created_at
    assert restored.started_at == query.started_at
    assert restored.completed_at == query.completed_at
    assert restored.execution_time == 2.0
    if empty_results:
        assert restored.response_entities == set()
        assert restored.derived_patterns == set()
        assert_current_scores(restored, 0.0, 0.0)
    else:
        assert restored.response_entities == {"one", "two"}
        assert restored.derived_patterns == {"pattern"}
        assert_current_scores(restored, 0.8, 1.0)


def test_rejected_transitions_do_not_ingest_results_or_change_state(
    query_clock
):
    query = iQuery()
    assert query.complete_execution([{"entity_id": "ignored"}]) is False
    assert query.results == []
    assert_current_scores(query, 0.0, 0.0)
    assert query.start_execution() is True
    query_clock.current += timedelta(seconds=2)
    assert query.complete_execution() is True
    assert_current_scores(query, 0.0, 0.0)
    snapshot = query.to_dict()

    assert query.complete_execution([{"entity_id": "ignored"}]) is False
    assert query.cancel_execution() is False
    assert query.start_execution() is False
    assert query.to_dict() == snapshot
