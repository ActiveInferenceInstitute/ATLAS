# InstituteOS integration — ATLAS

## Identity

| Field | Value |
| --- | --- |
| Repository | `ActiveInferenceInstitute/ATLAS` |
| Affiliation | `institute` |
| Category | `research` |
| Status | `active` |
| Maturity | `released` |
| Steward | Active Inference Institute |
| Default branch | `main` |
| Current release | — |
| License | `CC-BY-4.0` |
| Citation | Active Inference Institute — ATLAS. |

## Federation

| Setting | Value |
| --- | --- |
| Dashboard mode | `repos` |
| Analytics | `false` |
| Dashboard | `false` |
| Sync policy | `pull` |
| Registries | — |
| Tags | atlas, knowledge-management, python |

## Ecosystem relations

| Repository | Relation | Note |
| --- | --- | --- |
| `ActiveInferenceInstitute/InstituteOS` | `referenced-by` | Federated via the InstituteOS .aii manifest. |
| `docxology/ATLAS` | `references` | Public reference fork; the initial implementation was ported from it. |
| `ActiveInferenceInstitute/Generalized_Notation_Notation` | `references` | Ecosystem notation for active inference generative models; the docs link its integration guides at the pinned v5.0.3 revision. ATLAS carries no GNN model and no GNN dependency. |
| `ActiveInferenceInstitute/Active_Inference_Ontology` | `references` | Controlled vocabulary of active inference concepts; the docs link it. No ATLAS identifier mapping exists. |
| `ActiveInferenceInstitute/AEOS` | `references` | Domain ontology for scientific ecosystems; the docs link it. No ATLAS identifier mapping exists. |

## Key artifacts

| Path | Kind | Description |
| --- | --- | --- |
| `src/atlas` | `code` | ATLAS knowledge management package. |
| `tests` | `code` | Test suite. |
| `pyproject.toml` | `code` | Package metadata, dependency extras, and pytest configuration. |
| `README.md` | `doc` | Repository overview. |
| `docs/documentation-index.md` | `doc` | Documentation index. |
| `CITATION.cff` | `doc` | Machine-readable citation metadata. |
| `AGENTS.md` | `doc` | Agent guidance. |
| `LICENSE` | `doc` | License. |
| `src` | `code` | Source tree. |
| `docs` | `doc` | Documentation tree. |

## Portable tasks

| Task | Command | Working directory | Description |
| --- | --- | --- | --- |
| `inventory` | `git ls-files` | `.` | List tracked files. |
| `validate` | `python -m aii_platform.aii_sidecar.validate . --completeness` | `.` | Validate this sidecar against the aii-sidecar/v1 schema. |
| `lint` | `./gate lint` | `.` | Run the lint arm (flake8 fatal-error codes). |
| `qa` | `./gate docs` | `.` | Run the docs arm (whitespace, links, YAML, generated page). |
| `test` | `./gate test` | `.` | Run the full test suite. |
| `gnn` | `./gate gnn` | `.` | Run the pinned GNN conformance arm (needs network). |

## Validation

```bash
python -m aii_platform.aii_sidecar.validate <repo> --completeness
python -m aii_platform.aii_sidecar docs <repo> --overwrite
python -m aii_platform.aii_sidecar.run <repo> --list
```

The sidecar is valid when `validate` prints `OK` and reports no missing artifact,
manifest, link, or declared-doc path. Completeness is a curation target, not a
runtime requirement.

## Data boundary

This sidecar carries metadata only. It does not grant execution permission, does not
replace the repository's own documentation, and must not be used to move private
content into a public repository. Task execution is limited to trusted checkouts.
