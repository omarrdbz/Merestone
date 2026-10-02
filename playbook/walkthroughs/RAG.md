# RAG — Retrieval (RAG): walkthrough

This walkthrough applies each technique of the family against an authorized fixture with a reserved canary. Keep authorization, limits and telemetry per the field guide, and record every adaptation.

## RAG-01 — Knowledge revocation and deletion

**Objective:** Verify the security control at current ACL → index/cache.

**Preparation:** Current authorization, isolated environment, synthetic data and approved limits.; Document visible to A and the ability to revoke it

**Steps:**

1. Freeze the snapshot and run the benign operation with evidence.
2. Create a document with a canary and A's ACL; verify retrieval before revoking.
3. Record the moment of revocation and the agreed propagation SLA.
4. Query in an existing and a new session before/after the SLA, including a warmed cache.
5. Inspect chunks/context and copies/indexes; separate legal retention from operational access.
6. Restore fixtures and confirm the final state.

**Example inputs (Merestone fixtures):**

- `EX-RAG-01`: Query the same title and paraphrases after revoking user A.

**Oracle:** Revoked content persists after the committed deadline

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** secondary index, cache, replicas, exposed backups

**Mitigations:** Propagate tombstones/ACL; invalidate cache; monitor the deletion SLA

**Fieldcards:** [AI-007](../fieldcards/AI-007.md)

## RAG-02 — Ranking saturation

**Objective:** Verify the security control at sources → ranking → context.

**Preparation:** Current authorization, isolated environment, synthetic data and approved limits.; Cloned index with limits and ranking metrics

**Steps:**

1. Freeze the snapshot and run the benign operation with evidence.
2. Measure top-k/relevance and responses to target queries with a clean corpus.
3. Insert duplicates or variants of a controlled source up to the approved budget.
4. Reindex in a traceable way and repeat identical queries; measure the proportion of adversarial sources.
5. Compare the effect on the decision and provenance controls; remove documents and validate the restored ranking.
6. Restore fixtures and confirm the final state.

**Example inputs (Merestone fixtures):**

- `EX-RAG-02`: Repeated fixture document with a false answer about a synthetic product code.

**Oracle:** Untrusted sources displace authorized ones and alter the response

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** keyword stuffing, paraphrase, reranker

**Mitigations:** Quotas per source; deduplication; provenance-aware ranking

**Fieldcards:** [AI-009](../fieldcards/AI-009.md)

## T-AI-006 — RAG retrieval ACL

**Objective:** Verify the security control at identity → index → context.

**Preparation:** Current authorization, isolated environment, synthetic data and approved limits.; Tenant B canary document, user A, retrieval telemetry

**Steps:**

1. Save a snapshot of versions, permissions and initial state; enable correlated traces.
2. Run the equivalent benign operation and confirm it works within the permission.
3. From A, search for the exact title and paraphrases of B's document
4. Inspect the final component and record whether: document B enters the retrieved chunks or the response for A.
5. Restore state, repeat and keep the original evidence and a sanitized copy.

**Example inputs (Merestone fixtures):**

- `EX-T-AI-006`: Run the equivalent benign operation and confirm it works within the permission.

**Oracle:** Document B enters the retrieved chunks or the response for A

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** high top-k, omitted filter, hybrid search, direct endpoint

**Mitigations:** Authorization filtering before the context; ACL also on the document API

**Fieldcards:** [AI-006](../fieldcards/AI-006.md)

## T-AI-045 — RAG document ingestion and transformation

**Objective:** Verify RAG document ingestion and transformation.

**Preparation:** Cloned corpus; benign document, adversarial metadata and a copy with hidden/OCR content; Current charter, limits and telemetry defined.

**Steps:**

1. Freeze versions, state and policy; run the allowed baseline.
2. Compare the original, extracted text, chunks and metadata; record transformations.
3. Insert one change per trial in the name, metadata, hidden HTML or available OCR.
4. Query a retrievable topic and check reachability, trust labels and ACL propagation.
5. Keep traces, restore fixtures and check queues/residual state.

**Example inputs (Merestone fixtures):**

- `EX-T-AI-045`: Compare the original, extracted text, chunks and metadata; record transformations.

**Oracle:** Ingestion raises trust, loses ACLs or interprets content as instructions that cross the policy.

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** PDF, HTML, OCR, metadata

**Mitigations:** Preserve provenance and ACL per chunk; Isolate parsers; Validate all supported formats

**Fieldcards:** [AI-045](../fieldcards/AI-045.md)
