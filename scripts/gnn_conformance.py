#!/usr/bin/env python3
"""GNN conformance check against the pinned importer.

Single implementation of the ``gnn conformance (pinned)`` job: the local gate
arm (``./gate gnn``) and CI (``.github/workflows/gate.yml``) run this exact
file, so the check has one definition.

It reads ``.github/gnn-pin.json`` (schema ``gnn-importer-pin/v1``), installs
the pinned parser revision with ``--no-deps`` plus the runtime dependencies the
parser imports (skipped when that exact version is already importable), then
parses and type-checks every ``*.gnn.md`` sketch in the repository. When the repository carries no sketch, the pinned upstream
``input/gnn_files/basics/static_perception.md`` exemplar is checked instead:
that is a pipeline and pin conformance baseline, not a claim that ATLAS
contains a generative model.

Both the parser install and the exemplar fetch need network access, so this
arm is not part of ``./gate all``. Pass ``--no-install`` to use a parser that
is already installed at the pinned version.

Exit code is non-zero on any failure. See ``docs/gate.md`` and
``.github/GNN.md``.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIN_PATH = ROOT / ".github" / "gnn-pin.json"
SCHEMA = "gnn-importer-pin/v1"
PARSER_REPOSITORY = "ActiveInferenceInstitute/Generalized_Notation_Notation"
# Runtime dependencies the pinned parser imports; CI installed them separately
# because the parser itself is installed with --no-deps.
PARSER_RUNTIME_DEPS = ("defusedxml", "psutil", "pyyaml")


class ConformanceError(RuntimeError):
    """A pin, parser, or model check failed."""


def read_pin() -> dict:
    if not PIN_PATH.is_file():
        raise ConformanceError(f"missing pin file {PIN_PATH.relative_to(ROOT)}")
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    if pin.get("schema") != SCHEMA:
        raise ConformanceError(
            f"{PIN_PATH.relative_to(ROOT)}: schema {pin.get('schema')!r} != {SCHEMA!r}"
        )
    if pin.get("repository") != PARSER_REPOSITORY:
        raise ConformanceError(
            f"{PIN_PATH.relative_to(ROOT)}: repository {pin.get('repository')!r} "
            f"!= {PARSER_REPOSITORY!r}"
        )
    for key in ("revision", "tag"):
        if not pin.get(key):
            raise ConformanceError(f"{PIN_PATH.relative_to(ROOT)}: missing {key!r}")
    return pin


def parser_spec(pin: dict) -> str:
    return (
        f"generalized-notation-notation @ "
        f"git+https://github.com/{pin['repository']}.git@{pin['revision']}"
    )


def installed_version() -> str | None:
    """Version of an importable ``gnn`` package, or None when it cannot be used."""
    try:
        from gnn import __version__

        return __version__
    except Exception:  # ImportError, or a parser whose imports are broken
        return None


def install_parser(pin: dict) -> None:
    pip = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    subprocess.check_call([*pip, *PARSER_RUNTIME_DEPS])
    subprocess.check_call([*pip, "--no-deps", parser_spec(pin)])


def import_parser() -> tuple[str, object, object, object]:
    try:
        from gnn import __version__ as gnn_version
        from gnn.parsers.basic import parse_gnn_formal, validate_gnn_syntax
        from gnn.type_checker import GNNTypeChecker
    except ImportError as exc:  # pragma: no cover - environment failure
        raise ConformanceError(
            f"pinned GNN parser is not importable ({exc}); "
            "run without --no-install to install it"
        ) from exc
    return gnn_version, parse_gnn_formal, validate_gnn_syntax, GNNTypeChecker


def check_model(
    model: pathlib.Path,
    parse_gnn_formal,
    validate_gnn_syntax,
    GNNTypeChecker,
) -> None:
    parsed = parse_gnn_formal(model)
    if parsed is None or getattr(parsed, "parse_errors", None):
        raise ConformanceError(f"{model.name} did not parse cleanly")
    valid, errors = validate_gnn_syntax(model.read_text(encoding="utf-8"))
    if not valid:
        raise ConformanceError(f"{model.name} syntax errors: {errors!r}")
    with tempfile.TemporaryDirectory(prefix="gnn-conformance-") as output_dir:
        model_dir = pathlib.Path(output_dir) / "models"
        model_dir.mkdir()
        shutil.copy2(model, model_dir / model.name)
        # The pinned type checker returns 2 for warnings; only a falsy result is
        # treated as clean. This matches the historical CI behaviour and the
        # known caveat recorded in TO-DO.md.
        if not GNNTypeChecker().validate_gnn_files(model_dir, pathlib.Path(output_dir)):
            raise ConformanceError(f"GNN type checker rejected {model.name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="use an already installed pinned parser instead of installing it",
    )
    args = parser.parse_args(argv)

    try:
        pin = read_pin()
        expected_version = pin["tag"].removeprefix("v")
        if not args.no_install and installed_version() != expected_version:
            install_parser(pin)
        gnn_version, parse_gnn_formal, validate_gnn_syntax, GNNTypeChecker = import_parser()
        expected_version = pin["tag"].removeprefix("v")
        if gnn_version != expected_version:
            raise ConformanceError(
                f"installed GNN {gnn_version!r} does not match {pin['tag']!r}"
            )

        sketches = sorted(ROOT.rglob("*.gnn.md"))
        if sketches:
            for sketch in sketches:
                check_model(
                    sketch, parse_gnn_formal, validate_gnn_syntax, GNNTypeChecker
                )
            checked = len(sketches)
            source = "repository"
        else:
            exemplar_url = (
                "https://raw.githubusercontent.com/"
                f"{pin['repository']}/{pin['revision']}/input/gnn_files/basics/static_perception.md"
            )
            with tempfile.TemporaryDirectory(prefix="pinned-exemplar-") as tmp:
                exemplar = pathlib.Path(tmp) / "static_perception.md"
                urllib.request.urlretrieve(exemplar_url, exemplar)
                check_model(
                    exemplar, parse_gnn_formal, validate_gnn_syntax, GNNTypeChecker
                )
            checked = 1
            source = "pinned-exemplar"
    except (ConformanceError, subprocess.CalledProcessError, OSError) as exc:
        print(f"gnn conformance failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "gnn-version": gnn_version,
                "pin-revision": pin["revision"],
                "models": checked,
                "source": source,
                "result": "verified",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
