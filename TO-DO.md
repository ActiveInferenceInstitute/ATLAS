# ATLAS — Documentation To-Do

Last reviewed: 2026-08-02 (third pass: QA gate, CI, and working
conventions; see [REVIEW_LOG_2026-08-02.md](REVIEW_LOG_2026-08-02.md)).

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

## Medium

- [x] README rewritten as a complete, accurate repository overview grounded
      in repo state and the Institute's public Open Source Map — `README.md`
      ✓ `a8854b5`
- [x] Add machine-readable citation metadata (CITATION.cff) — ✓ `84b3c03`
- [x] Add contribution guide (CONTRIBUTING.md) — ✓ `84b3c03`
- [x] Add docs/ with a documentation index — `docs/index.md` ✓ `acbcef2`
- [x] Add this TO-DO file scoping all review findings ✓ `4e0ad77`
- [x] Record the review pass in REVIEW_LOG_2026-08-02.md ✓ `4e0ad77`
- [x] Add research-grounded About page (classification, status, ecosystem
      context, license) — `docs/overview.md` ✓ `0bdaeb8`
- [x] Add field-by-field .aii sidecar reference against the InstituteOS
      schema — `docs/metadata.md` ✓ `0bdaeb8`
- [x] Add quickstart guide — `docs/quickstart.md` ✓ `0bdaeb8`
- [x] Add security policy — `SECURITY.md` ✓ `fb466e7`
- [x] Add GitHub issue and pull request templates — `.github/` ✓ `fb466e7`
- [x] Enrich `.aii/config.yaml` to the documented `aii-sidecar/v1` schema
      (identity, affiliation, status, integration, validate task) with only
      values true of this repository — ✓ `298f121`
- [x] Add documentation QA gate (whitespace, links/anchors, YAML) and the
      `docs-qa` CI workflow — `scripts/docs_qa.py`,
      `.github/workflows/docs-qa.yml` ✓ `af83058`
- [x] Add agent/contributor working conventions — `AGENTS.md` ✓ `871af5b`
- [x] Add `.aii/docs/README.md`, declare it in the sidecar `docs` field, and
      add the `qa` portable task — ✓ `a5753ba`
- [x] Wire the QA gate and conventions into README (badge, layout, quality
      gate), SECURITY.md (private vulnerability reporting enabled), and the
      metadata reference — ✓ `1fd4d19`

## Major

- [x] Full documentation set (quickstart, usage, configuration reference,
      contribution guide) — completed to the extent possible without
      content: quickstart, sidecar configuration reference, and contribution
      guide now exist (`docs/`). Architecture and API documentation remain
      deferred until the repository gains code or project content — see the
      open list.

## Open / deferred

- Architecture and API documentation — deferred until the repository gains
  code or project content; writing them now would require fabrication.
- Content port decision: the public reference fork
  ([docxology/ATLAS](https://github.com/docxology/ATLAS)) contains an ATLAS
  Knowledge Management System implementation, but its content is not
  verified, and its headers state the MIT license while this repository is
  CC-BY-4.0. Porting requires a steward decision on provenance and license
  reconciliation. Documented in `docs/overview.md`; not ported.
- GitHub repository description on github.com still reads "ATLAS " (stub) —
  update via the repository settings page; not a commit-level change.
  Attempted via `gh repo edit` on 2026-08-02: denied (HTTP 404, this token
  has WRITE permission, not admin). Requires a steward with admin access.
- GitHub repository topics are not set (sibling repos use e.g.
  `active-inference`, `inference`); adding them requires admin access —
  steward action.
- Authoritative sidecar validation: run InstituteOS's own validator
  (`python -m instituteos.platform.aii_sidecar.validate .`) and its CI gate
  on the enriched sidecar when available; local verification (YAML parse +
  documented schema fields) passed on 2026-08-02.
