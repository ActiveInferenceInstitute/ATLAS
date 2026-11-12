# GNN conformance

`gnn conformance (pinned)` is the display name of the `gnn-conformance` job in
[`workflows/gate.yml`](workflows/gate.yml). It runs one command, `./gate gnn`,
which executes [`../scripts/gnn_conformance.py`](../scripts/gnn_conformance.py) —
the same file a developer runs locally, so the check has a single definition.

## Pin

The canonical pin is [`gnn-pin.json`](gnn-pin.json), schema
`gnn-importer-pin/v1`:

| Field | Value |
| --- | --- |
| `repository` | `ActiveInferenceInstitute/Generalized_Notation_Notation` |
| `tag` | `v5.0.3` |
| `revision` | `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` |

The check reads the pin rather than duplicating it: it refuses a pin whose
schema or repository differs, installs the parser from the pinned revision with
`--no-deps` plus the runtime modules the parser imports (skipping the install
when that exact version is already importable), and fails when the installed
version does not match `tag`.

## What it parses

1. Every `*.gnn.md` sketch in the repository, recursively. Each is parsed, its
   syntax validated, and the set type-checked by the pinned GNN type checker.
2. When the repository has no sketch — the current state — the pinned upstream
   `input/gnn_files/basics/static_perception.md` exemplar at the pinned revision
   is parsed and type-checked instead.

The second path is a pipeline and pin conformance baseline, not a claim that
this repository contains a generative model. ATLAS carries no GNN model and no
GNN dependency; the run installs the parser into the environment it is invoked
from, and the pin is never changed to make a check pass.

The receipt printed on success is JSON:
`{"gnn-version", "pin-revision", "models", "source", "result"}`, where `source`
is `repository` or `pinned-exemplar`.

## Known caveat

The pinned type checker returns the integer `2` for a warnings-only result and
`2` is truthy, so a warnings-only run is indistinguishable from a clean pass.
This is upstream behaviour at the pinned revision; `TO-DO.md` tracks it. Do not
change the pin to work around it.
