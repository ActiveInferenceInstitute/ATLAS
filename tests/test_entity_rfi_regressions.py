"""Regression contracts for persisted RFI identity and resolution."""

import json
import re

import pytest

from atlas.entities.attribute import Attribute
from atlas.entities.entity import Entity
from atlas.patterns.pattern import Pattern


@pytest.mark.parametrize(
    ("entity_id", "attribute_key"),
    [
        ("complete_test", "empty_field"),
        ("simple", "field"),
        ("prefix_with__underscores_", "_field__with_tail_"),
        ("complete_test", ""),
    ],
)
def test_rfi_resolves_exact_attribute_without_changing_id_schema(
    entity_id, attribute_key
):
    entity = Entity(entity_id=entity_id, attributes={attribute_key: None})
    rfis = entity.call_rfis()
    assert len(rfis) == 1
    rfi_id = next(iter(rfis))
    assert re.fullmatch(
        re.escape(f"rfi_{entity_id}_{attribute_key}_") + r"[0-9a-f]{8}",
        rfi_id,
    )
    version = entity.metadata.version

    assert entity.resolve_rfi(rfi_id, "resolved") is True
    assert entity.attributes == {attribute_key: "resolved"}
    assert "test" not in entity.attributes
    assert entity.get_pending_rfis() == set()
    assert entity.metadata.version == version + 1
    assert entity.resolve_rfi(rfi_id, "second response") is False
    assert entity.attributes == {attribute_key: "resolved"}
    assert entity.metadata.version == version + 1


@pytest.mark.parametrize(
    ("entity_type", "constructor_args"),
    [
        (Entity, {"entity_id": "complete_test"}),
        (
            Pattern,
            {
                "pattern_id": "complete_test",
                "qkit": ["query_one"],
                "parents": ["parent_one"],
                "children": ["child_one"],
            },
        ),
        (
            Attribute,
            {
                "attribute_id": "complete_test",
                "ref_id": "reference_one",
                "value": "attribute value",
                "data_type": "string",
            },
        ),
    ],
)
def test_pending_rfi_round_trip_uses_existing_entity_subclass_schema(
    entity_type, constructor_args
):
    entity = entity_type(
        **constructor_args,
        attributes={"empty_field": None, "kept": "value"},
        patterns=["assigned_pattern"],
    )
    entity.metadata.tags.add("tag")
    entity.mark_anomaly("query_one", "reason")
    entity.mark_exception("query_two", "exception")
    rfi_id = next(iter(entity.call_rfis()))
    payload = json.loads(json.dumps(entity.to_dict()))
    assert payload["pending_rfis"] == [rfi_id]

    restored = entity_type.from_dict(payload)
    assert type(restored) is entity_type
    assert restored.to_dict() == payload
    assert restored.resolve_rfi(rfi_id, "restored response") is True
    assert restored.attributes == {
        "empty_field": "restored response",
        "kept": "value",
    }
    assert restored.get_pending_rfis() == set()
    assert restored.patterns == ["assigned_pattern"]
    assert restored.get_anomalies() == {"query_one": "reason"}
    assert restored.get_exceptions() == {"query_two": "exception"}
    assert restored.metadata.tags == {"tag"}
    assert entity.attributes["empty_field"] is None
    assert entity.get_pending_rfis() == {rfi_id}


@pytest.mark.parametrize(
    "rfi_id",
    [
        "rfi_other_entity_empty_field_1234abcd",
        "rfi_complete_test_missing_field_1234abcd",
        "rfi_complete_test_empty_field_notauuid",
        "rfi_complete_test_empty_field_1234abc",
        "rfi_complete_test_empty_field_1234abcde",
        "rfi_complete_test_empty_field",
        "complete_test_empty_field_1234abcd",
    ],
)
def test_invalid_persisted_association_remains_pending(rfi_id):
    payload = Entity(
        entity_id="complete_test", attributes={"empty_field": None}
    ).to_dict()
    payload["pending_rfis"] = [rfi_id]
    entity = Entity.from_dict(payload)
    version = entity.metadata.version
    updated_at = entity.metadata.updated_at

    assert entity.resolve_rfi(rfi_id, "must not be written") is False
    assert entity.attributes == {"empty_field": None}
    assert entity.get_pending_rfis() == {rfi_id}
    assert entity.metadata.version == version
    assert entity.metadata.updated_at == updated_at


def test_removed_attribute_does_not_redirect_or_consume_pending_rfi():
    entity = Entity(
        entity_id="complete_test", attributes={"empty_field": None}
    )
    rfi_id = next(iter(entity.call_rfis()))
    assert entity.remove_attribute("empty_field") is True

    assert entity.resolve_rfi(rfi_id, "response") is False
    assert entity.attributes == {}
    assert entity.get_pending_rfis() == {rfi_id}

    assert entity.add_attribute("empty_field", None) is True
    assert entity.resolve_rfi(rfi_id, "response") is True
    assert entity.attributes == {"empty_field": "response"}
    assert entity.get_pending_rfis() == set()


def test_failed_attribute_write_keeps_request_available_for_retry():
    class ReadOnlyAttributes(dict):
        def __setitem__(self, key, value):
            raise TypeError("Attributes are read-only")

    entity = Entity(
        entity_id="complete_test",
        attributes=ReadOnlyAttributes(empty_field=None),
    )
    rfi_id = next(iter(entity.call_rfis()))
    version = entity.metadata.version

    assert entity.resolve_rfi(rfi_id, "response") is False
    assert entity.attributes == {"empty_field": None}
    assert entity.get_pending_rfis() == {rfi_id}
    assert entity.metadata.version == version

    entity.attributes = dict(entity.attributes)
    assert entity.resolve_rfi(rfi_id, "response") is True
    assert entity.attributes == {"empty_field": "response"}
    assert entity.get_pending_rfis() == set()
    assert entity.metadata.version == version + 1


def test_raised_attribute_write_does_not_consume_pending_rfi():
    class WriteRefusingEntity(Entity):
        def add_attribute(self, key, value, overwrite=True):
            raise RuntimeError("Writes are unavailable")

    entity = WriteRefusingEntity(
        entity_id="complete_test", attributes={"empty_field": None}
    )
    rfi_id = next(iter(entity.call_rfis()))

    assert entity.resolve_rfi(rfi_id, "response") is False
    assert entity.attributes == {"empty_field": None}
    assert entity.get_pending_rfis() == {rfi_id}


def test_resolution_consumes_only_the_matching_pending_request():
    entity = Entity(
        entity_id="complete_test",
        attributes={"empty_field": None, "empty_field_suffix": "  "},
    )
    rfis = entity.call_rfis()
    assert len(rfis) == 2
    rfi_id = next(
        rfi for rfi in rfis
        if rfi.rpartition("_")[0] == "rfi_complete_test_empty_field"
    )

    assert entity.resolve_rfi(rfi_id, "response") is True
    assert entity.attributes == {
        "empty_field": "response",
        "empty_field_suffix": "  ",
    }
    assert entity.get_pending_rfis() == rfis - {rfi_id}


def test_nonpending_request_cannot_write_even_with_valid_identity():
    entity = Entity(
        entity_id="complete_test", attributes={"empty_field": None}
    )
    assert entity.resolve_rfi(
        "rfi_complete_test_empty_field_1234abcd", "response"
    ) is False
    assert entity.attributes == {"empty_field": None}
    assert entity.get_pending_rfis() == set()
