# TOOLS — Functions and actions

## Preparation and inventory

Registry of tools, schemas, dispatchers, identities, roles, resources, arguments, approvals, ledger and backends. Prepare reversible operations and A/B accounts.

## Walkthrough

1. Test the backend and the dispatcher directly before attempting LLM induction.
2. Compare name/type/schema and argument semantics; validate objects, properties, paths and destinations.
3. Verify the effective user's permissions, not an identity declared in text.
4. Test intent scope and approval bound to arguments, time and session.
5. Check the persisted effect and retries; repeat E2E if an LLM is in scope.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-014](../fieldcards/AI-014.md) | Action without approval | TEST |
| [AI-015](../fieldcards/AI-015.md) | Excessive tool privileges | TEST |
| [AI-042](../fieldcards/AI-042.md) | SSRF in a URL retrieval tool | TEST |
| [AI-043](../fieldcards/AI-043.md) | Tool arguments and dispatcher | TEST |
| [AI-044](../fieldcards/AI-044.md) | Binding and validity of human approval | TEST |
| [AI-056](../fieldcards/AI-056.md) | Tool file path and workspace | TEST |

## Interpretation and limits

A well-formed call can be improper. A registered function can have SQLi or command injection in its implementation. The model rejecting an input does not fix the backend.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
