# PLATFORM — Application, deployment and operation

## Preparation and inventory

APIs, IAM, secrets, logs, network, containers, serving, CI/CD, registries and AIBOM. Incorporate a current AppSec/infra assessment with explicit scope/versions.

## Walkthrough

1. Test object and property authorization directly and through the AI integration if it exists.
2. Verify exposure of logs/errors and access to secrets with the workload's real identity.
3. Check provenance, dependencies, admission and rollback to revoked versions.
4. Measure quotas, egress and isolation within the approved budget.
5. Generate a fixture event to check alerting, triage, revocation and recovery.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-025](../fieldcards/AI-025.md) | API object authorization | TEST |
| [AI-026](../fieldcards/AI-026.md) | API properties and role | TEST |
| [AI-028](../fieldcards/AI-028.md) | Sensitive logs and telemetry | TEST |
| [AI-033](../fieldcards/AI-033.md) | Dependencies and provenance | TEST |
| [AI-034](../fieldcards/AI-034.md) | Deployment secrets and identity | TEST |
| [AI-035](../fieldcards/AI-035.md) | Execution isolation | TEST |
| [AI-036](../fieldcards/AI-036.md) | Deployment admission and rollback | TEST |
| [AI-053](../fieldcards/AI-053.md) | Detection of and response to boundary violations | TEST |
| [AI-057](../fieldcards/AI-057.md) | Integrity of adapters, tokenizer and embeddings | TEST |

## Interpretation and limits

Do not replace classic tests with an OWASP LLM list. A historical CVE requires the relevant version/configuration/advisory; do not infer exploitation from the package name.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
