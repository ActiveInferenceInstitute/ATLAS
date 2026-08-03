# REVIEW LOG — 2026-08-02

Mega-deep documentation review of the ATLAS repository
(ActiveInferenceInstitute/ATLAS), docs-deep pass.

## Phase 0 — Preflight

- Branch: `main` (origin/HEAD → origin/main). Default branch confirmed via
  `git symbolic-ref --short refs/remotes/origin/HEAD`.
- `git fetch origin` + `git pull --ff-only`: already up to date.
- HEAD at start: `77dd26a` "add .aii sidecar (100% complete) + CC-BY-4.0
  LICENSE (InstituteOS metadata)". Working tree clean.
- Inventory (tracked files only):
  - `.aii/config.yaml` — InstituteOS metadata sidecar (schema
    `instituteos.platform.aii_sidecar`); category research, steward Active
    Inference Institute, license CC-BY-4.0, citation "Active Inference
    Institute — ATLAS.", capabilities: documentation.
  - `.gitignore` — standard Python template.
  - `LICENSE` — CC-BY-4.0 with SPDX identifier.
  - `README.md` — two-line stub ("# ATLAS" / "ATLAS " with trailing space).
- No `docs/`, no AGENTS.md/CLAUDE.md, no TODO/ROADMAP files, no CI config,
  no `.github/`, no code of any kind.

## Phase 1 — Mega-deep docs review

Grounding verified during review:

- Institute Open Source Map (https://activeinference.institute/knowledge/)
  classifies ATLAS as a *project materials repository* in the *open-source
  projects* family; both org website URLs return HTTP 200.
- InstituteOS repo (https://github.com/ActiveInferenceInstitute/InstituteOS),
  referenced by the sidecar, exists publicly.
- Initial commit date 2024-08-21 (df461c8) — used as CITATION.cff
  `date-released`.

Findings by severity:

- Minor
  1. README is a stub with trailing whitespace on line 2.
  2. No license reference from README.
  3. No citation metadata (no CITATION.cff).
  4. No repository/website links in README.
  5. GitHub repo description on the site still reads "ATLAS " (settings-level,
     not commit-level — deferred to steward).
- Medium
  1. README rewrite: complete, accurate overview grounded in repo state.
  2. Add CITATION.cff.
  3. Add CONTRIBUTING.md.
  4. Add docs/ with a documentation index.
  5. Add top-level TO-DO.md scoping all findings.
  6. Add this review log.
- Major
  1. Full documentation set (quickstart, usage, configuration reference,
     architecture overview) — cannot be written honestly: the repository
     contains no code or content yet. Deferred until content lands.

Not run (explicitly skipped): no test suites or linters exist in the repo
(no Python/other code); external link checks done via curl for the two org
URLs used in docs.

## Phase 3 — Implementation

| Commit | Change |
| --- | --- |
| a8854b5 | docs: rewrite README as accurate repository overview |
| 84b3c03 | docs: add citation metadata and contribution guide |
| acbcef2 | docs: add documentation index under docs/ |

Additional commits appended below as the pass progresses.

## Phase 4 — Final verification & push

- Verification: no trailing whitespace in any markdown file; all relative
  links in README.md, CONTRIBUTING.md, TO-DO.md, REVIEW_LOG, and
  docs/index.md resolve; no broken in-page anchors; org website URLs return
  HTTP 200 (curl). `git status` contained only the intended changes.
- Commits: a8854b5, 84b3c03, acbcef2, 4e0ad77 (four commits; six files
  changed in total: README.md, CITATION.cff, CONTRIBUTING.md,
  docs/index.md, TO-DO.md, and this log).
- Pushed to `main` (`77dd26a..4e0ad77`); `git status` confirms up to date
  with origin/main.

---

## Second pass — 2026-08-02 (post-push continuation)

Follow-up pass driven by the directive to proceed with all updates and
research directions ambitiously and comprehensively.

### Research findings (all verified against public sources)

- The Institute's public Open Source Map
  (https://activeinference.institute/knowledge/) classifies ATLAS as a
  *project materials repository* in the *open-source projects* family; the
  public Directory
  (https://activeinference.institute/directory/) lists it under the same
  classification.
- The Directory states the Institute's default license for public materials
  is CC BY-NC-SA 4.0 and that specific products may use different terms;
  ATLAS's LICENSE (CC-BY-4.0) is such a per-repository choice and is
  authoritative for this repository.
- InstituteOS documents the `.aii` sidecar convention publicly
  (docs/reference/modules/platform/aii_sidecar.md): schema `aii-sidecar/v1`,
  validation via `python -m instituteos.platform.aii_sidecar.validate
  <repo>`, and a 100%-completeness CI gate for reference sidecars.
- A public fork of this repository (docxology/ATLAS, created 2024-08-21,
  minutes after this repo's initial commit; last pushed 2025-06-15) contains
  an "ATLAS Knowledge Management System" implementation in Python
  (src/atlas package, tests, examples, doc/ tree). Its own documentation
  makes unverified claims (version/status headers) and states the MIT
  license.

### Decisions

- **Not ported:** the fork's content was NOT merged into this public
  repository. Provenance is unverified (no prior work trail), the fork's
  claims are unendorsed, and its MIT headers conflict with this repo's
  CC-BY-4.0. The relationship is documented factually in docs/overview.md
  with cited sources; a port decision is left open in TO-DO.md for the
  steward.
- **Sidecar enriched:** `.aii/config.yaml` was aligned with the documented
  `aii-sidecar/v1` schema, mirroring InstituteOS's own sidecar and the
  Active_Inference_Ontology exemplar, using only values true of this
  repository (default_branch main, affiliation institute, status wip,
  maturity experimental, empty release placeholders, integration
  analytics/dashboard false + sync pull, added validate task). Authoritative
  validation remains InstituteOS's validator/CI gate.
- **Docs expanded:** research-grounded About page (with a verified citation
  ledger and Sources blocks), sidecar metadata reference, quickstart,
  security policy, and GitHub issue/PR templates.

### Implementation

| Commit | Change |
| --- | --- |
| 0bdaeb8 | docs: expand documentation set with research-grounded guides |
| fb466e7 | docs: add security policy and issue/PR templates |
| 298f121 | chore(aii): align sidecar with documented aii-sidecar/v1 schema |

Additional commits appended below.

### Verification (second pass)

- Citation ledger (grounded-citations skill): 4 sources registered, verbatim
  evidence quotes attached; docs/overview.md, docs/metadata.md and
  docs/quickstart.md pass structural + evidence verification (ids valid,
  Sources blocks consistent, every cited source carries verbatim evidence).
- No trailing whitespace in any .md/.yaml file; no broken relative links
  across all docs; sidecar parses as YAML with the 11 documented top-level
  keys (ruby psych).
- Not run: InstituteOS validator (repo too large to clone locally for the
  check; noted as an open item for the InstituteOS CI gate). No test suites
  exist in this repository.

## Phase 4 (second pass) — Final verification & push

- Verification: no trailing whitespace in any .md/.yaml/.cff file; all
  relative links across the full doc set resolve; sidecar parses as YAML
  (ruby psych) with the documented top-level keys; citation ledger
  structural + evidence checks pass for the three research-grounded docs.
  `git status` contained only the intended changes.
- Commits: 0bdaeb8, fb466e7, 298f121, 749f661 (four commits; eleven files
  changed: README.md, docs/index.md, docs/overview.md, docs/metadata.md,
  docs/quickstart.md, SECURITY.md, .github/ISSUE_TEMPLATE.md,
  .github/PULL_REQUEST_TEMPLATE.md, .aii/config.yaml, TO-DO.md, and this
  log).
- Pushed to `main` (`573b466..749f661`); `git status` confirms up to date
  with origin/main.
