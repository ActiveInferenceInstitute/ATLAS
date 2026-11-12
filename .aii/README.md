# .aii — InstituteOS sidecar

This folder is the committed [InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS)
sidecar for **`ActiveInferenceInstitute/ATLAS`**. It records curated institutional metadata that the GitHub
API cannot provide — identity, category, maturity, ecosystem relations, key artifacts,
provenance, and portable tasks — so InstituteOS can federate a unified view across
Institute repositories without touching this project's own content. The schema is
`aii-sidecar/v1`.

## Contents

| File | Purpose |
| --- | --- |
| [`config.yaml`](config.yaml) | Machine-readable metadata; the single source of truth. |
| [`readiness.json`](readiness.json) | Declared tier, baseline commit, and waivers for the AII readiness standard. |
| [`docs/`](docs/README.md) | Sidecar documents: the [`README.md`](docs/README.md) · [`AGENTS.md`](docs/AGENTS.md) folder guides, and [`INTEGRATION.md`](docs/INTEGRATION.md) — how this repository is federated, validated, and operated through InstituteOS. |
| [`README.md`](README.md) · [`AGENTS.md`](AGENTS.md) | Human and agent guidance for this folder. |

## Repository profile

| Field | Value |
| --- | --- |
| Repository | `ActiveInferenceInstitute/ATLAS` |
| Category | `research` |
| Status | `active` |
| Maturity | `released` |
| License | `CC-BY-4.0` |
| Default branch | `main` |
| Homepage | https://github.com/ActiveInferenceInstitute/ATLAS |
| Tags | `atlas`, `knowledge-management`, `python` |

## Capabilities

- python
- knowledge-management
- documentation
- python-package
- tested
- ci
- citation

## Portable tasks

| Task | Command | Working directory | Description |
| --- | --- | --- | --- |
| `inventory` | `git ls-files` | `.` | List tracked files. |
| `validate` | `python -m aii_platform.aii_sidecar.validate . --completeness` | `.` | Validate this sidecar against the aii-sidecar/v1 schema. |
| `setup` | `./gate setup` | `.` | Install the gate environment (needs network on first run). |
| `lint` | `./gate lint` | `.` | Run the lint arm (flake8 fatal-error codes). |
| `qa` | `./gate docs` | `.` | Check docs/documentation-index.md, documentation QA, the Publishing artifact digests, and the generated gate page. No manuscript command. |
| `fast` | `./gate fast` | `.` | Run the test suite without the slow marker. |
| `test` | `./gate test` | `.` | Run the full test suite. |
| `gnn` | `./gate gnn` | `.` | Run GNN conformance against .github/gnn-pin.json (needs network). |
| `all` | `./gate all` | `.` | Run the offline lint, docs, and full test arms. |
| `measure` | `./gate measure` | `.` | Refresh the generated gate measurements. |

## Links

- **docs:** docs/documentation-index.md
- **github:** https://github.com/ActiveInferenceInstitute/ATLAS
- **homepage:** https://github.com/ActiveInferenceInstitute/ATLAS
- **website:** https://www.activeinference.org

## Validate

The authoritative validator ships in the private `aii-platform` kernel:

```bash
python -m aii_platform.aii_sidecar.validate <repo> --completeness
python -m aii_platform.aii_sidecar docs <repo> --overwrite
python -m aii_platform.aii_sidecar.run <repo> --list
```

If the private environment is unavailable, review `config.yaml` as plain YAML and
check that every declared path exists in the repository.
