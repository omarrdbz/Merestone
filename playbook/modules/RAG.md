# RAG — Retrieval and knowledge

## Preparation and inventory

Sources, ingestion, parsers, OCR if present, chunks, embedding/reranker, indexes, ACLs, cache, citations and revocation SLA. Prepare public/private A/B documents with canaries and a cloned corpus.

## Walkthrough

1. Map original document → extraction → chunk/ACL → ranking → context → response.
2. Test the ACL before the context, a cache warmed by another actor and revocation after the SLA.
3. Evaluate adversarial documents and hidden content; demonstrate that the material was retrieved.
4. Compare poisoned sources, ranking saturation and citations with a corpus baseline.
5. If there are tools/egress, run a composite scenario; if not, measure response integrity/confidentiality.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-002](../fieldcards/AI-002.md) | Indirect injection in RAG | TEST |
| [AI-006](../fieldcards/AI-006.md) | RAG retrieval ACL | TEST |
| [AI-007](../fieldcards/AI-007.md) | Knowledge revocation and deletion | TEST |
| [AI-008](../fieldcards/AI-008.md) | Poisoning of a retrievable source | TEST |
| [AI-009](../fieldcards/AI-009.md) | Ranking saturation | TEST |
| [AI-029](../fieldcards/AI-029.md) | RAG chain to simulated exfiltration | TEST |
| [AI-045](../fieldcards/AI-045.md) | RAG document ingestion and transformation | TEST |

## Interpretation and limits

A final response without the secret does not demonstrate an ACL before the model. A document that was not retrieved does not prove resistance to its content. Knowledge poisoning and prompt injection may need different causes/corrections.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
