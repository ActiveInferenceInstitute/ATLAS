# Repository metadata (.aii sidecar)

`.aii/` is a standalone, committed folder present in every Active Inference
Institute repository — "like `.github/`, but for InstituteOS" — carrying
curated metadata that the GitHub API cannot provide (identity, affiliation,
category, status, ecosystem links, tags).[3]

The sidecar follows the `aii-sidecar/v1` schema and is validated by the
InstituteOS platform: `python -m instituteos.platform.aii_sidecar.validate
<repo>`.[3] This page documents the fields present in this repository's
`.aii/config.yaml` as of 2026-08-02.

## Field reference

| Field | Meaning (per schema docs) | Value in this repository |
| --- | --- | --- |
| `schema` | Sidecar schema identifier | `aii-sidecar/v1` |
| `meta.sidecar_version` | Sidecar spec version | `1.0.0` |
| `meta.updated` | Last sidecar update | `2026-08-02` |
| `repo.name` / `slug` | Repository name and slug | `ATLAS` / `atlas` |
| `repo.full_name` | GitHub full name | `ActiveInferenceInstitute/ATLAS` |
| `repo.description` | Curated one-line description | `Project materials repository of the Active Inference Institute.` |
| `repo.default_branch` | Default branch | `main` |
| `repo.homepage` | Repository homepage | `https://github.com/ActiveInferenceInstitute/ATLAS` |
| `institute.affiliation` | institute \| ecosystem | `institute` |
| `institute.category` | InstituteOS domain | `research` |
| `institute.status` | active \| wip \| archived \| deprecated | `wip` |
| `institute.maturity` | experimental \| wip \| released \| stable | `experimental` |
| `institute.steward` | Stewarding body | `Active Inference Institute` |
| `ecosystem.relations` | Cross-repo relations | `referenced-by` `ActiveInferenceInstitute/InstituteOS` (federated via the `.aii` manifest) |
| `ecosystem.links` | Curated links | github, website (`https://www.activeinference.org`) |
| `artifacts` | Declared artifacts | `README.md` (doc) |
| `provenance.license` | License | `CC-BY-4.0` |
| `provenance.citation.text` | Citation string | `Active Inference Institute — ATLAS.` |
| `provenance.current_release` / `releases_manifest` | Release metadata | none (empty) |
| `instituteos.dashboard_mode` | Dashboard mode | `repos` |
| `instituteos.registries` | Registry memberships | none |
| `instituteos.tags` | Tags | `atlas` |
| `capabilities` | Declared capabilities | `documentation` |
| `tasks` | Portable runnable ops | `inventory` (`git ls-files`), `validate` (sidecar schema validation) |

## Validation

The authoritative check for the sidecar is the InstituteOS validator
(`python -m instituteos.platform.aii_sidecar.validate .` from the repository
root, with the `instituteos` package installed), which InstituteOS runs as a
CI gate on reference sidecars.[3]

## Sources

[3] https://github.com/ActiveInferenceInstitute/InstituteOS/blob/main/docs/reference/modules/platform/aii_sidecar.md — InstituteOS — aii_sidecar schema documentation
