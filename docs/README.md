# `docs/` — documentation tree

Guides for ATLAS, one topic per file. The canonical entry point and full table
of contents is [`index.md`](index.md); this folder guide only orients a reader
who opened the directory directly.

| Document | Use it for |
| --- | --- |
| [`index.md`](index.md) | The documentation index: every guide and source reference in one place. |
| [`overview.md`](overview.md) | What ATLAS is, its classification and status, ecosystem context, and license. |
| [`architecture.md`](architecture.md) | Module map and design of the `atlas` package. |
| [`api.md`](api.md) | Public API, class by class. |
| [`usage.md`](usage.md) | Install, quick start, and a walkthrough with verified snippets. |
| [`quickstart.md`](quickstart.md) | Clone, inspect, validate, and contribute. |
| [`applied-active-inference.md`](applied-active-inference.md) | Where the inquiry loop matches the active inference framing and where it does not. |
| [`metadata.md`](metadata.md) | The `.aii` sidecar, field by field, against the InstituteOS schema. |

All links here and in the guides are checked by
[`../scripts/docs_qa.py`](../scripts/docs_qa.py), the repository's
documentation QA gate. Add a new guide to [`index.md`](index.md) when you add
one here, and keep claims grounded in the committed code.
