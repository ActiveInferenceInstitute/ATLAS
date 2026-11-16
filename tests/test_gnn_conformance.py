"""Regression coverage for the pinned GNN conformance result contract.

``GNNTypeChecker.validate_gnn_files`` returns the pipeline exit sentinel, not a
boolean: ``True`` (exit 0), ``2`` (SUCCESS_WITH_WARNINGS — one or more files
had type/consistency problems, or no GNN file was found), ``False`` (exit 1).
``2`` is truthy, so a truthiness test reports an invalid model as verified.
These cases pin the decision point without needing the pinned parser or network
access: ``check_model`` receives the parser functions as arguments.
"""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "gnn_conformance", ROOT / "scripts/gnn_conformance.py"
)
gnn_conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gnn_conformance)

REVISION = "75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf"
OLDER_REVISION = "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1"


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
    path.write_text(
        "# GNN Example: fixture\n\n## StateSpaceBlock\n\nA[2,2,type=float]\n",
        encoding="utf-8",
    )
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


@pytest.fixture
def importer_pin(tmp_path, monkeypatch):
    pin_path = tmp_path / ".github" / "gnn-pin.json"
    pin_path.parent.mkdir()
    pin = {
        "schema": gnn_conformance.SCHEMA,
        "repository": gnn_conformance.PARSER_REPOSITORY,
        "revision": REVISION,
        "tag": "v5.1.0",
    }
    pin_path.write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(gnn_conformance, "ROOT", tmp_path)
    monkeypatch.setattr(gnn_conformance, "PIN_PATH", pin_path)
    return pin_path, pin


def test_old_release_refuses_before_install(importer_pin, capsys):
    path, pin = importer_pin
    path.write_text(
        json.dumps(dict(pin, revision=OLDER_REVISION, tag="v5.0.3")), encoding="utf-8"
    )

    assert gnn_conformance.main([]) == 1
    assert "requires GNN v5.1.0 or later" in capsys.readouterr().err


@pytest.mark.parametrize(
    "origin, commit",
    [
        ("ActiveInferenceInstitute/Generalized_Notation_Notation", OLDER_REVISION),
        ("other/Generalized_Notation_Notation", REVISION),
    ],
)
def test_no_install_refuses_mismatched_provenance(
    importer_pin, monkeypatch, capsys, origin, commit
):
    monkeypatch.setattr(
        gnn_conformance,
        "installed_provenance",
        lambda: {
            "url": f"https://github.com/{origin}.git",
            "vcs_info": {"vcs": "git", "commit_id": commit},
        },
    )

    assert gnn_conformance.main(["--no-install"]) == 1
    assert "--no-install refuses this environment" in capsys.readouterr().err


def test_shared_reader_selects_specs_and_preserves_pinned_exemplar(
    importer_pin, model, monkeypatch, capsys
):
    pin_path, pin = importer_pin
    downloaded = []
    specs = [model.name]
    findings = []

    def check_importer(root, **options):
        assert root == pin_path.parents[1]
        assert options == {
            "pin_path": pin_path,
            "expected_repository": pin["repository"],
            "expected_commit": REVISION,
            "expected_tag": pin["tag"],
            "require_pointer": True,
            "pointer_workflow": ".github/workflows/gate.yml",
            "pointer_job": "gnn-conformance",
            "validate_specs": False,
        }
        return {
            "ok": not findings,
            "pin": pin,
            "specs": {"files": specs},
            "findings": findings,
        }

    def fetch_exemplar(url, target):
        downloaded.append(url)
        target.write_bytes(model.read_bytes())

    monkeypatch.setattr(gnn_conformance, "provenance_check", lambda pin: (REVISION, ""))
    monkeypatch.setattr(
        gnn_conformance,
        "import_parser",
        lambda: (
            "5.1.0",
            check_importer,
            _parse_ok,
            _syntax_ok,
            _checker_returning(True),
        ),
    )
    monkeypatch.setattr(gnn_conformance.urllib.request, "urlretrieve", fetch_exemplar)

    assert gnn_conformance.main(["--no-install"]) == 0
    assert json.loads(capsys.readouterr().out)["source"] == "repository"
    assert not downloaded
    specs.clear()
    assert gnn_conformance.main(["--no-install"]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["models"] == 1
    assert receipt["source"] == "pinned-exemplar"
    assert downloaded == [
        f"https://raw.githubusercontent.com/{pin['repository']}/{REVISION}/input/gnn_files/basics/static_perception.md"
    ]
    findings.append({"level": "error", "message": "GNN pointer does not name the pin"})
    assert gnn_conformance.main(["--no-install"]) == 1
    assert "GNN pointer does not name the pin" in capsys.readouterr().err
    assert len(downloaded) == 1
