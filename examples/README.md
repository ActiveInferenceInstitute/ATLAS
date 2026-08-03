# ATLAS Examples

This directory contains runnable examples for the ATLAS knowledge management
system.

## Contents

- `basic/basic_test.py` — end-to-end exercise of core ATLAS functionality
  (entities, attributes, patterns, queries, interfaces, serialization).
  Run from the repository root:

  ```bash
  python examples/basic/basic_test.py
  ```

  Pass `--output-dir DIR` to save the test summary elsewhere (the summary is
  written to `basic_test_results.json` in the given directory).

- `advanced/comprehensive_demo.py` — full-featured demonstration including
  optional visualization (requires the visualization dependencies; install
  them with `pip install -e ".[viz]"`).

## Notes

- Run the examples from the repository root so the `src/` layout is found,
  or install the package first: `pip install -e .`.
- The examples import ATLAS through `sys.path` and do not require the
  package to be installed.
