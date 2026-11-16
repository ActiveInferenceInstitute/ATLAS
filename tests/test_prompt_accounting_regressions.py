"""Regression contracts for local prompt-interface terminal accounting."""

import pytest

from atlas.interfaces.prompt_interface import SimpleTransformInterface


def assert_accounting(interface, uses, errors):
    expected_rate = (uses - errors) / uses if uses else 0.0
    assert interface.usage_count == uses
    assert interface.error_count == errors
    assert interface.success_rate == pytest.approx(expected_rate)
    statistics = interface.get_statistics()
    assert statistics["usage_count"] == uses
    assert statistics["error_count"] == errors
    assert statistics["success_rate"] == pytest.approx(expected_rate)


def make_local_interface():
    def transform(data):
        if data == "transform-error":
            raise ValueError("Local transformation failed")
        if data == "invalid-output":
            return 42
        return data.upper()

    return SimpleTransformInterface(
        transform,
        input_schema={"type": "str"},
        output_schema={"type": "str"},
    )


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (42, "Input validation failed"),
        ("invalid-output", "Output validation failed"),
        ("transform-error", "Local transformation failed"),
    ],
)
def test_success_then_failure_updates_field_and_statistics(data, error):
    interface = make_local_interface()
    assert_accounting(interface, 0, 0)
    assert interface.execute("success") == {
        "success": True, "error": None, "data": "SUCCESS"
    }
    assert_accounting(interface, 1, 0)

    assert interface.execute(data) == {
        "success": False, "error": error, "data": None
    }
    assert_accounting(interface, 2, 1)
    assert interface.success_rate == 0.5

    assert interface.execute("recovery") == {
        "success": True, "error": None, "data": "RECOVERY"
    }
    assert_accounting(interface, 3, 1)


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (42, "Input validation failed"),
        ("invalid-output", "Output validation failed"),
        ("transform-error", "Local transformation failed"),
    ],
)
def test_first_failure_counts_one_use_and_one_error(data, error):
    interface = make_local_interface()
    assert interface.execute(data) == {
        "success": False, "error": error, "data": None
    }
    assert_accounting(interface, 1, 1)


def test_mixed_terminal_outcomes_count_once_per_execution():
    interface = make_local_interface()
    outcomes = [
        ("one", {"success": True, "error": None, "data": "ONE"}, 0),
        (
            42,
            {
                "success": False,
                "error": "Input validation failed",
                "data": None,
            },
            1,
        ),
        (
            "invalid-output",
            {
                "success": False,
                "error": "Output validation failed",
                "data": None,
            },
            2,
        ),
        (
            "transform-error",
            {
                "success": False,
                "error": "Local transformation failed",
                "data": None,
            },
            3,
        ),
        ("two", {"success": True, "error": None, "data": "TWO"}, 3),
    ]
    for uses, (data, expected, errors) in enumerate(outcomes, start=1):
        assert interface.execute(data, context={"local": True}) == expected
        assert_accounting(interface, uses, errors)
    assert interface.get_statistics()["has_input_schema"] is True
    assert interface.get_statistics()["has_output_schema"] is True


@pytest.mark.parametrize("stage", ["input", "output"])
def test_validation_exceptions_preserve_failure_shape_and_accounting(stage):
    class RaisingValidator(SimpleTransformInterface):
        def validate_input(self, data):
            if stage == "input" and data == "reject":
                raise RuntimeError("Input validator unavailable")
            return super().validate_input(data)

        def validate_output(self, data):
            if stage == "output" and data == "reject":
                raise RuntimeError("Output validator unavailable")
            return super().validate_output(data)

    interface = RaisingValidator(lambda data: data)
    assert interface.execute("accepted") == {
        "success": True, "error": None, "data": "accepted"
    }
    assert_accounting(interface, 1, 0)
    assert interface.execute("reject") == {
        "success": False,
        "error": f"{stage.title()} validator unavailable",
        "data": None,
    }
    assert_accounting(interface, 2, 1)
    assert interface.execute("accepted again")["success"] is True
    assert_accounting(interface, 3, 1)
