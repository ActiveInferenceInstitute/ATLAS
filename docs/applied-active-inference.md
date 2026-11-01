# Applied active inference framing

This page states, precisely, where ATLAS's question-oriented discovery
connects to the active inference framing used across the Institute's
repositories, and where it does not. Every claim below refers to the code in
`src/atlas/` as committed.

## The inquiry loop as implemented

1. A question is registered through `ATLASEngine.add_query` or constructed as
   an `iQuery` with query text, target patterns, context, and a priority
   (`QueryPriority`: `LOW`, `NORMAL`, `HIGH`, `URGENT`).
2. Execution has an explicit lifecycle: `start_execution` moves the query from
   `PENDING` to `EXECUTING`; `complete_execution`, `fail_execution`, and
   `cancel_execution` close it. Results, responding entities, and derived
   patterns are recorded on the query.
3. Candidate information sources are the registered entities, patterns, and
   queries. `ATLASEngine.query()` selects those whose text matches (all query
   words present, an exact phrase, or an exact key) and ranks them by a
   relevance score: exact value `1.0`, substring `0.5`, exact key `0.3`, key
   substring `0.1`.
4. Two heuristics summarize each finished inquiry.
   `iQuery.calculate_quality_score()` sums a result-count term (up to `0.4`),
   responding-entity diversity (up to `0.3`), discovered patterns (up to
   `0.2`), and `0.1` when execution took under five seconds.
   `iQuery.calculate_confidence_score()` is a `0.5` baseline plus `0.1`–`0.3`
   for multiple results plus `0.2` when patterns were derived, capped at `1.0`.
5. Pattern structure is maintained independently by `PatternEngine`:
   `calculate_pattern_similarity()` is a weighted Jaccard score
   (`0.5` × question-kit overlap + `0.3` × attribute-key overlap + `0.2` ×
   shared-ancestor overlap), with clustering, merge suggestions, and usage
   analysis built on top.

## Where the framing genuinely fits

- **Question-oriented discovery is a decision process over information
  sources.** Deciding which question to pursue, which sources to query, and
  when to stop has the same shape as policy selection over epistemic actions.
  ATLAS keeps that shape explicit and inspectable: statuses, priorities,
  results, and derived patterns are recorded on the query and in the graph
  rather than hidden inside a pipeline.
- **Structure before inference.** Typed relationships, pattern hierarchies,
  and attribute records make the structure of a knowledge domain queryable.
  Making that structure explicit is a prerequisite for any model-based
  treatment of inquiry.
- **Explicit weights.** Priorities and the quality/confidence formulas above
  are declared arithmetic, so a reader can recompute and challenge every
  score.

## Where the framing does not apply

- ATLAS does not implement a generative model, and it does not minimize free
  energy or expected free energy. `ATLASEngine.query()` is lexical matching;
  relevance, quality, and confidence are the fixed heuristics stated above,
  not posterior beliefs or precision estimates.
- `iQuery.calculate_confidence_score()` is a monotone function of result count
  and derived patterns. It is not calibrated against outcomes, and this
  repository makes no calibration claim for it.
- ATLAS carries no GNN model file, no state-space matrices, and no ontology
  annotation surface. Generative-model specification belongs to
  [GNN](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
  (see its
  [integration guides](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/tree/8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1/docs/gnn/integration));
  the shared controlled vocabulary belongs to
  [Active_Inference_Ontology](https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology);
  the domain ontology of scientific entities and interaction motifs belongs to
  [AEOS](https://github.com/ActiveInferenceInstitute/AEOS).

## Using this framing honestly

- Use it to explain why ATLAS records priorities, statuses, and confidence
  values, and how its discovery loop relates to model-based work. Do not cite
  it as evidence that ATLAS performs Bayesian inference.
- If the lexical heuristics are ever replaced with model-based scoring, record
  the new formulas and their validation before upgrading this page.

See also: [architecture](architecture.md) for the module map,
[usage](usage.md) for runnable examples, and [overview](overview.md) for the
repository's place in the Institute ecosystem.
