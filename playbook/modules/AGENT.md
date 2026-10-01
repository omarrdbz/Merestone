# AGENT — Autonomy, memory and delegation

## Preparation and inventory

Planner, objective, delegations, credentials, memory/TTL, triggers, queues, fan-out, limits, cancellation and approvals. Memory is evaluated even without an agent.

## Walkthrough

1. Define the legitimate action and the allowed degree of autonomy; distinguish general permission from the task's intent.
2. Test persistence of adversarial notes across sessions and separation of scope/author.
3. Verify that delegation preserves the user's restrictions and does not inherit higher privileges.
4. Simulate a commit with a lost response and retry, concurrency and parent cancellation.
5. Test a scheduled event after revocation; measure pending effects and restoration.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-005](../fieldcards/AI-005.md) | Contaminated persistent memory | TEST |
| [AI-016](../fieldcards/AI-016.md) | Agent resources and loops | TEST |
| [AI-017](../fieldcards/AI-017.md) | Retry and idempotency | TEST |
| [AI-018](../fieldcards/AI-018.md) | Delegation between agents | TEST |
| [AI-051](../fieldcards/AI-051.md) | Distributed budget, queues and cancellation | TEST |
| [AI-058](../fieldcards/AI-058.md) | Memory isolation and lifecycle | TEST |
| [AI-059](../fieldcards/AI-059.md) | External triggers and scheduled tasks | TEST |

## Interpretation and limits

Do not model an agent as just a chat. A good final response can hide intermediate actions. The absence of a loop does not make memory or scheduled tasks irrelevant.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
