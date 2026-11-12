# ATLAS — Publishing member contract

The [Publishing contract](https://github.com/ActiveInferenceInstitute/ActiveInferenceJournal/blob/d8ec888a8f3051a66bed9af047ee4b206050bdce/docs/workflows/publishing.md)
in ActiveInferenceJournal owns record identity and the migration rules. This page
records ATLAS's member facts and pinned artifacts, not another identity grammar.

## Member facts

| Fact | ATLAS value |
| --- | --- |
| Gate | [`./gate`](../../gate) |
| Documented arms | `setup lint docs fast test gnn measure` |
| Docs index | [`docs/documentation-index.md`](../documentation-index.md) |
| Manuscript command | none |
| GNN pin | [`.github/gnn-pin.json`](../../.github/gnn-pin.json) |

[The sidecar](../../.aii/config.yaml) records a task per documented arm, plus the
existing `all` aggregate. Its docs task records the docs index and absence of a
manuscript command; its GNN task names the pin.

## Pinned canonical artifacts

Copied unchanged from ActiveInferenceJournal at
`d8ec888a8f3051a66bed9af047ee4b206050bdce`:

- [`record-identity.schema.json`](record-identity.schema.json) — canonical grammar.
- [`scripts/gate/identity.py`](../../scripts/gate/identity.py) — canonical checker.
- [`.github/gnn-pin.json`](../../.github/gnn-pin.json) — already identical to the lead pin.

```text
record-identity.schema.json  84f6c4df6efc3f15f0d8a9a05c8aabd0cbdc08b0f4feac5fcc8ae860a81e306b
identity.py  847328ff163fa90c869495164869caf4e83313748e8a444dbab8d4e459b11074
gnn-pin.json  eb83f7f1b73eb31e116bd05b1f457dd07e6874a2a4ba0e9e95e5bc91f094cd55
```

## Verification and scope

Run `./gate docs`. The existing docs arm runs the pinned checker to validate the
schema and all recorded digests, then runs its `--verify-copy` path for each
artifact above. It needs no network or JSON Schema package. A changed copy with
a stale digest fails; updates must come from the canonical source, including its
recorded digest, rather than blessing local changes.

As the lead contract directs, existing member checks are retained rather than
duplicated: ATLAS's arm registry, links/anchors, generated measurements, and GNN
conformance remain behind `./gate`. Lead-specific corpus, Journal-Utilities, and
network-dependent arms are not adopted. This migration does not invent ATLAS
records, manuscript output, or a corpus-completeness claim.
