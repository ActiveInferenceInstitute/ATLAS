# ATLAS — .aii sidecar documentation

`.aii/` is the InstituteOS metadata sidecar convention: a standalone,
committed folder present in every Active Inference Institute repository. It
carries curated metadata the GitHub API cannot provide (identity,
affiliation, category, status, ecosystem links, tags) so InstituteOS tooling
can federate a unified view across repositories.

For this repository:

- `.aii/config.yaml` — the sidecar itself (schema: `aii-sidecar/v1`).
- The full field-by-field reference lives in the repository docs:
  [docs/metadata.md](../docs/metadata.md).

Validate the sidecar with the InstituteOS CLI:

```bash
python -m instituteos.platform.aii_sidecar.validate .
```
