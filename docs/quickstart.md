# Quickstart

How to clone, inspect, and contribute to the ATLAS repository.

## Clone

```bash
git clone https://github.com/ActiveInferenceInstitute/ATLAS.git
cd ATLAS
```

## What is inside

| Path | Description |
| --- | --- |
| `README.md` | Repository overview. |
| `CONTRIBUTING.md` | How to contribute. |
| `CITATION.cff` | Machine-readable citation metadata. |
| `LICENSE` | CC-BY-4.0 license. |
| `SECURITY.md` | Security reporting. |
| `docs/` | Documentation index, overview, metadata reference, quickstart. |
| `TO-DO.md` | Scoped improvements and open items. |
| `.aii/config.yaml` | InstituteOS metadata sidecar. |

## Validate the metadata sidecar

The repository carries an InstituteOS sidecar validated against the
`aii-sidecar/v1` schema:

```bash
python -m instituteos.platform.aii_sidecar.validate .
```

This requires the `instituteos` package; see the InstituteOS documentation
for installation.[3] The sidecar also declares a portable task that lists
tracked files:

```bash
git ls-files
```

## Contribute

- Open an issue or pull request via GitHub; see
  [CONTRIBUTING.md](../CONTRIBUTING.md).
- Keep changes grounded: this repository is documentation-facing, and content
  must match the actual state of the repository.
- All contributions are licensed CC-BY-4.0.

## Cite

See [CITATION.cff](../CITATION.cff) or the README's citation section.

## Sources

[3] https://github.com/ActiveInferenceInstitute/InstituteOS/blob/main/docs/reference/modules/platform/aii_sidecar.md — InstituteOS — aii_sidecar schema documentation
