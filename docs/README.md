# `docs/` — documentation hub

Guides for ATLAS, one topic per file. This page is the hub: it says what the
tree contains, where the authoritative index lives, and how to verify the docs
before you commit.

## Start here

| Entry | Use it for |
| --- | --- |
| [`documentation-index.md`](documentation-index.md) | The flat index of every long-lived document in the repository. |
| [`overview.md`](overview.md) | What ATLAS is, its classification and status, ecosystem context, and license. |
| [`quickstart.md`](quickstart.md) | Clone, inspect, validate, and contribute. |
| [`gate.md`](gate.md) | The gate: one entry point for lint, docs, fast, full, and GNN conformance checks. |
| [`architecture.md`](architecture.md) | Module map and design of the `atlas` package. |
| [`api.md`](api.md) | Public API, class by class. |
| [`usage.md`](usage.md) | Install, quick start, and a walkthrough with verified snippets. |
| [`applied-active-inference.md`](applied-active-inference.md) | Where the inquiry loop matches the active inference framing and where it does not. |
| [`metadata.md`](metadata.md) | The `.aii` sidecar, field by field, against the InstituteOS schema. |

## How the tree is organised

- **Hub and index.** This page orients you; [`documentation-index.md`](documentation-index.md)
  is the flat index. A new long-lived document is added to the index, not to a
  second ad-hoc list.
- **One topic per file**, grounded in the committed code. When docs and code
  disagree, fix whichever is wrong; do not restate a claim the code does not
  support.
- **Generated pages.** [`_generated/`](_generated/GATE.md) holds facts a script
  produces — currently the gate arm timings. Regenerate instead of editing:
  numbers that a script can produce are never hand-written into prose.

## Verify the documentation

```bash
./gate docs
```

That arm runs [`../scripts/docs_qa.py`](../scripts/docs_qa.py) — trailing
whitespace, relative links and in-file anchors in markdown, and YAML
parseability of `.aii/config.yaml` and `CITATION.cff` — and then checks that
[`_generated/GATE.md`](_generated/GATE.md) still matches the gate's arm list.
CI runs the same arm; see [`gate.md`](gate.md).
