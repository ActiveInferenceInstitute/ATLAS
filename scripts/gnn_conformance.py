#!/usr/bin/env python3
"""GNN conformance check against the pinned importer.

Single implementation of the ``gnn conformance (pinned)`` job: the local gate
arm (``./gate gnn``) and CI (``.github/workflows/gate.yml``) run this exact
file, so the check has one definition.

It reads ``.github/gnn-pin.json`` (schema ``gnn-importer-pin/v1``) and installs
the pinned parser revision with ``--no-deps`` plus the runtime dependencies the
parser imports, then parses and type-checks every ``*.gnn.md`` sketch in the
repository.

An existing install is reused only when PEP 610 ``direct_url.json`` binds it to
the pinned repository *and* the pinned commit. A version string is not
provenance: another commit, a fork, or a wheel from an index can all report
``5.0.3``. ``--no-install`` applies the same requirement and fails rather than
keeping an already-importable but different parser. Provenance binds where the
distribution was installed from, not the bytes on disk. When the repository carries no sketch, the pinned upstream
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


DISTRIBUTION = "generalized-notation-notation"


def installed_version() -> str | None:
    """Version of an importable ``gnn`` package, or None when it cannot be used."""
    try:
        from gnn import __version__

        return __version__
    except Exception:  # ImportError, or a parser whose imports are broken
        return None


def installed_provenance() -> dict:
    """PEP 610 ``direct_url.json`` for the installed parser, or ``{}``.

    A wheel from an index carries no ``direct_url.json`` at all, so its origin
    cannot be checked and it is never treated as the pin.
    """
    try:
        from importlib.metadata import distribution

        raw = distribution(DISTRIBUTION).read_text("direct_url.json")
    except Exception:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_repository(url: str) -> str | None:
    """``https://host/owner/repo.git`` -> ``host/owner/repo``; None if not a URL."""
    value = url.strip().lower()
    for prefix in ("git+https://", "https://"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    else:
        return None
    return value.rstrip("/").removesuffix(".git")


def provenance_check(pin: dict) -> tuple[str | None, str]:
    """Return (installed commit, problem). A problem means the install is not the pin."""
    if not PIN_PATH.is_file():
        return None, "pin file missing"
    direct_url = installed_provenance()
    if not direct_url:
        return None, f"no PEP 610 direct_url.json for {DISTRIBUTION} (origin unknown)"
    vcs = direct_url.get("vcs_info") or {}
    if vcs.get("vcs") != "git":
        return None, f"installed from {direct_url.get('url')!r} without git metadata"
    commit = vcs.get("commit_id")
    if commit != pin["revision"]:
        return commit, f"installed commit {commit!r} is not the pinned revision {pin['revision']!r}"
    repository = normalize_repository(str(direct_url.get("url", "")))
    expected_repository = f"github.com/{pin['repository']}".lower()
    if repository != expected_repository:
        return commit, f"installed from {repository!r}, pin expects {expected_repository!r}"
    return commit, ""


def install_parser(pin: dict) -> None:
    pip = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    subprocess.check_call([*pip, *PARSER_RUNTIME_DEPS])
    # --force-reinstall: pip treats an installed 5.0.3 from another commit as
    # already satisfying the requirement, which would keep the wrong bytes.
    subprocess.check_call([*pip, "--no-deps", "--force-reinstall", parser_spec(pin)])


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
        # ``validate_gnn_files`` returns the pipeline exit sentinel, not a
        # boolean: ``True`` (exit 0), ``2`` (SUCCESS_WITH_WARNINGS — one or more
        # files had type/consistency problems, or no GNN file was found), and
        # ``False`` (exit 1). Only a literal ``True`` is a clean pass: ``2`` is
        # truthy, so a truthiness test would report an invalid model as verified.
        result = GNNTypeChecker().validate_gnn_files(model_dir, pathlib.Path(output_dir))
        if result is not True:
            raise ConformanceError(
                f"GNN type checker rejected {model.name}: "
                f"validate_gnn_files returned {result!r} (True alone is a clean pass)"
            )


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
        commit, problem = provenance_check(pin)
        if problem and args.no_install:
            raise ConformanceError(
                f"--no-install refuses this environment: {problem}; "
                "run without --no-install to install the pin"
            )
        if problem:
            install_parser(pin)
            commit, problem = provenance_check(pin)
            if problem:
                raise ConformanceError(f"after installing the pinned spec: {problem}")
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
                "install-commit": commit,
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
