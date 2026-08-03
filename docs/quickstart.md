# Quickstart

How to clone, inspect, test, and contribute to the ATLAS repository.

## Clone

```bash
git clone https://github.com/ActiveInferenceInstitute/ATLAS.git
cd ATLAS
```

## What is inside

| Path | Description |
| --- | --- |
| `src/atlas/` | The ATLAS package. |
| `tests/` | Test suite (run with pytest). |
| `examples/` | Runnable examples. |
| `README.md` | Repository overview. |
| `CONTRIBUTING.md` | How to contribute. |
| `CITATION.cff` | Machine-readable citation metadata. |
| `LICENSE` | CC-BY-4.0 license. |
| `SECURITY.md` | Security reporting. |
| `docs/` | Documentation index, overview, architecture, API, usage, metadata, quickstart. |
| `TO-DO.md` | Scoped improvements and open items. |
| `.aii/config.yaml` | InstituteOS metadata sidecar. |

## Install and test

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest pytest-cov
python -m pytest
```

See [docs/usage.md](usage.md) for a usage walkthrough.

## Validate the metadata sidecar

The repository carries an InstituteOS sidecar validated against the
`aii-sidecar/v1` schema:

```bash
python -m instituteos.platform.aii_sidecar.validate .
```

This requires the `instituteos` package; see the InstituteOS documentation
for installation.[3] The sidecar also declares portable tasks that list
tracked files and run the documentation QA gate:

```bash
git ls-files
python3 scripts/docs_qa.py
```

## Contribute

- Open an issue or pull request via GitHub; see
  [CONTRIBUTING.md](../CONTRIBUTING.md).
- Keep changes grounded: content must match the actual state of the
  repository, and the test suite must stay green.
- All contributions are licensed CC-BY-4.0.

## Cite

See [CITATION.cff](../CITATION.cff) or the README's citation section.
