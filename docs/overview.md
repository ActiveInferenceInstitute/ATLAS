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

As of 2026-08-02 the repository contains metadata and documentation only:

- `README.md` — repository overview.
- `LICENSE` — CC-BY-4.0 license.
- `CITATION.cff` — machine-readable citation metadata.
- `CONTRIBUTING.md` — contribution guide.
- `SECURITY.md` — security reporting.
- `docs/` — documentation index and guides (this page, metadata reference,
  quickstart).
- `TO-DO.md` — scoped improvements and open items.
- `.aii/config.yaml` — InstituteOS metadata sidecar.

No code or project content has been published in this repository. Its
history: initialized 2024-08-21, sidecar and license added 2026-06-30,
documentation pass on 2026-08-02 (see `REVIEW_LOG_2026-08-02.md`).

## Ecosystem context

- **InstituteOS federation.** The repository carries an InstituteOS metadata
  sidecar, and the sidecar declares that ATLAS is federated through the
  InstituteOS `.aii` manifest.[3]
- **Reference implementation.** A public fork of this repository
  ([docxology/ATLAS](https://github.com/docxology/ATLAS)) contains an "ATLAS
  Knowledge Management System" implementation, described there as "a
  comprehensive knowledge management framework with modular composability,
  dynamic pattern recognition, and question-oriented information
  discovery."[4] The fork was created 2024-08-21, minutes after this
  repository's initial commit, and was last updated 2025-06-15.[4] Its content
  has not been merged into this repository; claims made in the fork's own
  documentation are not verified by or endorsed in this repository, and the
  fork's headers state the MIT license, which differs from this repository's
  CC-BY-4.0 license.

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
