# ATLAS — Documentation To-Do

Last reviewed: 2026-08-02 (fourth pass: implementation port and complete
documentation; see [REVIEW_LOG_2026-08-02.md](REVIEW_LOG_2026-08-02.md)).

Scope definitions:

- **Minor** — typo, broken link, formatting, whitespace.
- **Medium** — stale-section rewrite, doc restructure, added missing guide.
- **Major** — large doc-system overhaul, new documentation site,
  cross-cutting refactor.

Completed items are marked ✓ with the implementing commit. Open / deferred
items are listed at the end.

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

- GitHub repository description on github.com still reads "ATLAS " (stub) —
  update via the repository settings page; not a commit-level change.
  Attempted via `gh repo edit` on 2026-08-02: denied (HTTP 404, this token
  has WRITE permission, not admin). Requires a steward with admin access.
- GitHub repository topics are not set (sibling repos use e.g.
  `active-inference`, `inference`); adding them requires admin access —
  steward action.
- Optional: run the viz-extras tests in CI (`pip install -e ".[viz]"` plus
  psutil and the obsidian extra) — the current CI runs the core suite only.
- Optional: publish `atlas-knowledge` to PyPI once a release is cut
  (the fork never published; packaging metadata is ready).
- Optional: upstream sync with the reference fork if it ever diverges again
  (last pushed 2025-06-15; the port took its current HEAD).
