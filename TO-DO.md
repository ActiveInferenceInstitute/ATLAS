# ATLAS — Documentation To-Do

Last reviewed: 2026-08-02 (mega-deep documentation review pass, see
[REVIEW_LOG_2026-08-02.md](REVIEW_LOG_2026-08-02.md)).

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
- [x] Add this TO-DO file scoping all review findings ✓ (this commit)
- [x] Record the review pass in REVIEW_LOG_2026-08-02.md ✓ (this commit)

## Major

- [ ] Full documentation set (quickstart, usage, configuration reference,
      architecture overview) — **deferred**: the repository contains no code
      or project content yet; writing such guides now would require
      fabrication. Add when actual content lands.

## Open / deferred

- Major: full documentation set — deferred until the repository gains
  content (see above).
- GitHub repository description on github.com still reads "ATLAS " (stub) —
  update via the repository settings page; not a commit-level change.
- `.aii/config.yaml` `description: ATLAS` is self-referential — left
  untouched; the file is InstituteOS-managed metadata (schema
  `instituteos.platform.aii_sidecar`) and is not governed by this repo's
  docs.
- SECURITY.md — not applicable until the repository contains code or
  user-facing content.
