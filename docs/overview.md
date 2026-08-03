# About ATLAS

This page records what the ATLAS repository is, what it currently contains,
and its place in the Active Inference Institute's public ecosystem. Every
external claim below is cited to a verifiable public source.

## What this repository is

ATLAS is a public repository of the Active Inference Institute, registered in
the Institute's Open Source Map as a *project materials repository* within the
*open-source projects* family.[1] The Institute's public Directory lists it
among the organization's repositories under the same classification.[2]

Repository-level affiliation and stewardship metadata is carried in the
InstituteOS sidecar (`.aii/config.yaml`), which records the Active Inference
Institute as steward and the repository's category as research.[3]

## Current contents and status

As of 2026-08-02 the repository contains the ATLAS knowledge management
system implementation plus metadata and documentation:

- `src/atlas/` — the ATLAS package (engine, entities, patterns, queries,
  interfaces, integrations, visualization, utils).
- `tests/` — test suite; `examples/` — runnable examples.
- `README.md`, `LICENSE` (CC-BY-4.0), `CITATION.cff`, `CONTRIBUTING.md`,
  `SECURITY.md`, `AGENTS.md`, `scripts/docs_qa.py`, `.github/` (templates
  and CI), `docs/` (index, overview, architecture, API, usage, metadata,
  quickstart), `TO-DO.md`, and the `.aii` metadata sidecar.

History: initialized 2024-08-21; sidecar and license added 2026-06-30;
documentation passes and the code port on 2026-08-02 (see
`REVIEW_LOG_2026-08-02.md`).

## Ecosystem context

- **InstituteOS federation.** The repository carries an InstituteOS metadata
  sidecar, and the sidecar declares that ATLAS is federated through the
  InstituteOS `.aii` manifest.[3]
- **Reference implementation and port.** A public fork of this repository
  ([docxology/ATLAS](https://github.com/docxology/ATLAS)) contained an
  "ATLAS Knowledge Management System" implementation, described there as "a
  comprehensive knowledge management framework with modular composability,
  dynamic pattern recognition, and question-oriented information
  discovery."[4] The fork was created 2024-08-21, minutes after this
  repository's initial commit, and was last updated 2025-06-15.[4]
  On 2026-08-02 the implementation was ported into this repository
  (curated: code, tests, and examples only) under this repository's
  CC-BY-4.0 license. The fork's own documentation was not ported: its
  claims (version/status headers such as "Production Ready", an
  aspirational Web UI and REST API, and assessment artifacts) were not
  verifiable against its code, and its headers stated the MIT license,
  which differs from this repository's CC-BY-4.0. The ported test suite was
  aligned with the actual code API, and the GraphML/GEXF export path was
  fixed during verification.

## License

This repository is licensed CC-BY-4.0; see `LICENSE`. Note that the
Institute's default license for public materials is CC BY-NC-SA 4.0, and the
Institute's public Directory states that "specific products and
collaborations may use different terms; check the individual repository or
resource for details."[2] The repository's `LICENSE` file is the authoritative
statement for ATLAS.

## Sources

[1] https://activeinference.institute/knowledge — Open Source Map — Active Inference Institute
[2] https://activeinference.institute/directory — Directory — Active Inference Institute
[3] https://github.com/ActiveInferenceInstitute/InstituteOS/blob/main/docs/reference/modules/platform/aii_sidecar.md — InstituteOS — aii_sidecar schema documentation
[4] https://github.com/docxology/ATLAS — docxology/ATLAS — public fork (reference implementation)
