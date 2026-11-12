"""Regression coverage for the pinned GNN conformance result contract.

``GNNTypeChecker.validate_gnn_files`` returns the pipeline exit sentinel, not a
boolean: ``True`` (exit 0), ``2`` (SUCCESS_WITH_WARNINGS — one or more files
had type/consistency problems, or no GNN file was found), ``False`` (exit 1).
``2`` is truthy, so a truthiness test reports an invalid model as verified.
These cases pin the decision point without needing the pinned parser or network
access: ``check_model`` receives the parser functions as arguments.
"""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "gnn_conformance", ROOT / "scripts/gnn_conformance.py"
)
gnn_conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gnn_conformance)


class _Parsed:
    """Stand-in for a parser result with no parse errors."""

    parse_errors = []


def _parse_ok(model):
    return _Parsed()


def _syntax_ok(content):
    return True, []


def _checker_returning(value):
    class Checker:
        def validate_gnn_files(self, model_dir, output_dir):
            return value

    return Checker


@pytest.fixture
def model(tmp_path):
    path = tmp_path / "static_perception.gnn.md"
    path.write_text("# GNN Example: fixture\n\n## StateSpaceBlock\n\nA[2,2,type=float]\n",
                   encoding="utf-8")
    return path


def test_true_result_is_accepted(model):
    gnn_conformance.check_model(model, _parse_ok, _syntax_ok, _checker_returning(True))


@pytest.mark.parametrize("result", [2, False, None, 0])
def test_non_true_result_is_refused_and_reported(model, result):
    with pytest.raises(gnn_conformance.ConformanceError) as excinfo:
        gnn_conformance.check_model(
            model, _parse_ok, _syntax_ok, _checker_returning(result)
        )
    message = str(excinfo.value)
    assert model.name in message
    assert repr(result) in message
