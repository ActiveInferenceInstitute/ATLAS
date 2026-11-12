# ATLAS — Documentation To-Do

Last reviewed: 2026-11-01 (fifth pass: GNN alignment, currency, and
optional-dependency coverage; see
[REVIEW_LOG_2026-11-01.md](REVIEW_LOG_2026-11-01.md)).

Scope definitions:

- **Minor** — typo, broken link, formatting, whitespace.
- **Medium** — stale-section rewrite, doc restructure, added missing guide.
- **Major** — large doc-system overhaul, new documentation site,
  cross-cutting refactor.

Completed items are marked ✓ with the implementing commit. Open / deferred
items are listed at the end.

## Fifth pass (2026-11-01)

- [x] **Optional-dependency tests now run green.** The Obsidian vault parser
      no longer records `Templates/*.md` as notes (it collected them twice,
      once as notes and once as templates), and CI installs
      `.[test,viz,obsidian]`, so the previously skipped visualization,
      Obsidian, and memory-instrumentation tests execute.
- [x] **Packaging consolidated.** `setup.py` is removed; `pyproject.toml` is
      the only metadata home (PEP 621 project metadata, dependency extras,
      pytest configuration) and declares `requires-python = ">=3.11"`.
- [x] **Dependencies corrected.** `python-dateutil` was declared but never
      imported; `numpy` is only used by `atlas.visualization`; `PyYAML` and
      `requests` are used by the Obsidian integration and the HTTP interface
      but were undeclared. Core is now `networkx`, with `viz`, `obsidian`,
      `http`, `test`, and `dev` extras.
- [x] **CI currency.** `actions/checkout@v7`, `actions/setup-python@v7`,
      least-privilege permissions, job timeouts, and a Python 3.11/3.14
      matrix.
- [x] **Test hygiene.** `tests/run_single_test.py` no longer exposes `test_*`
      functions that return booleans, removing the pytest collection warning.
- [x] **Applied active inference framing documented.**
      `docs/applied-active-inference.md` states the inquiry loop as
      implemented, where it matches the active inference framing, and where it
      does not (lexical heuristics, no free energy, no calibration claim).
- [x] **Signposting.** README, AGENTS.md, the docs index, and the sidecar link
      GNN's integration guides (pinned v5.0.3), the Active Inference
      Ontology, and AEOS; the sidecar records the three relations explicitly.

## Minor

- [x] README stub content ("# ATLAS" / bare "ATLAS " line with trailing
      whitespace) replaced by a full overview — `README.md` ✓ `a8854b5`
- [x] No license reference from README — `README.md` ✓ `a8854b5`
- [x] No citation info in README — `README.md` ✓ `a8854b5`
- [x] No repository/website links in README — `README.md` ✓ `a8854b5`
- [x] Trailing whitespace stripped from all ported Python files (41 files)
      ✓ `f717245`

## Medium

- [x] README rewritten as a complete, accurate repository overview grounded
      in repo state and the Institute's public Open Source Map — `README.md`
      ✓ `a8854b5`
- [x] Add machine-readable citation metadata (CITATION.cff) — ✓ `84b3c03`
- [x] Add contribution guide (CONTRIBUTING.md) — ✓ `84b3c03`
- [x] Add docs/ with a documentation index — `docs/index.md` ✓ `acbcef2`
- [x] Add this TO-DO file scoping all review findings ✓ `4e0ad77`
- [x] Record the review pass in REVIEW_LOG_2026-08-02.md ✓ `4e0ad77`
- [x] Add research-grounded About page — `docs/overview.md` ✓ `0bdaeb8`
- [x] Add field-by-field .aii sidecar reference — `docs/metadata.md`
      ✓ `0bdaeb8`
- [x] Add quickstart guide — `docs/quickstart.md` ✓ `0bdaeb8`
- [x] Add security policy — `SECURITY.md` ✓ `fb466e7`
- [x] Add GitHub issue and pull request templates — `.github/` ✓ `fb466e7`
- [x] Enrich `.aii/config.yaml` to the documented `aii-sidecar/v1` schema
      — ✓ `298f121`
- [x] Add documentation QA gate and `docs-qa` CI workflow — ✓ `af83058`
- [x] Add agent/contributor working conventions — `AGENTS.md` ✓ `871af5b`
- [x] Add `.aii/docs/README.md`, declare it in the sidecar `docs` field, and
      add the `qa` portable task — ✓ `a5753ba`
- [x] Wire the QA gate and conventions into README, SECURITY.md, and the
      metadata reference — ✓ `1fd4d19`
- [x] Add architecture guide grounded in the ported code — `docs/architecture.md`
      ✓ `76ddac6`
- [x] Add class-by-class API reference — `docs/api.md` ✓ `76ddac6`
- [x] Add usage guide with verified code snippets — `docs/usage.md`
      ✓ `76ddac6`
- [x] Update README and existing docs for the ported codebase — ✓ `6d4cbe0`

## Major

- [x] Full documentation set (quickstart, usage, configuration reference,
      architecture, API) — completed: see `docs/` (index, overview,
      architecture, api, usage, metadata, quickstart).
- [x] Implementation port decision — resolved by evidence: the public
      reference fork's code was verified (81 passing tests after aligning
      drifted tests), license-normalized to CC-BY-4.0, and ported; the
      fork's unverifiable documentation was not ported ✓ `f717245`
      (see `docs/overview.md` "Reference implementation and port").
- [x] Authoritative sidecar validation — InstituteOS validator run:
      "OK: . has a valid .aii sidecar"; doctor completeness 100%
      (standard met: True) ✓ `5d7fee2`

## Open / deferred

- GNN conformance warning sentinel. The pinned `gnn conformance (pinned)` job
  ([`.github/GNN.md`](.github/GNN.md),
  [`.github/workflows/tests.yml`](.github/workflows/tests.yml)) treats the
  return value of `GNNTypeChecker().validate_gnn_files(...)` as a boolean
  (`if not ...: raise`). The upstream checker returns the integer `2` to signal
  warnings, and `2` is truthy in Python, so a warning-only result is
  indistinguishable from a clean pass. This is upstream behavior in the pinned
  `Generalized_Notation_Notation` revision
  `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1` (v5.0.3); do not change the pin to
  "fix" it. Track it upstream and, if a stricter check is wanted, compare the
  return value explicitly (`!= 0`) rather than relying on truthiness.
- GitHub repository description and topics: verified 2026-11-01 with
  `gh api repos/ActiveInferenceInstitute/ATLAS` that the description reads
  "Adaptive Thinking and Learning Architecture System: a question-oriented
  knowledge management framework with entities, patterns, a graph-backed
  query engine, and pluggable interfaces, from the Active Inference
  Institute." and that topics are set (`graph-database`,
  `information-retrieval`, `knowledge-graph`, `knowledge-management`,
  `networkx`, `python`, `question-answering`). The two earlier steward-action
  items are therefore closed.
- Optional: publish `atlas-knowledge` to PyPI once a release is cut
  (the fork never published; packaging metadata is ready).
- Optional: upstream sync with the reference fork if it ever diverges again
  (last pushed 2025-06-15; the port took its current HEAD).
- Optional: `atlas.visualization` (about 3,100 lines across five modules)
  still has parallel figure helpers; a consolidation pass would reduce it
  but is not attempted here because the module surface is not exercised by
  any consumer contract. The parallel color-scheme helpers were consolidated
  (2026-11-06): the five scheme dictionaries now live as named constants in
  `atlas/visualization/common.py`, each class references the constants, and
  the values are unchanged (test suite green).
