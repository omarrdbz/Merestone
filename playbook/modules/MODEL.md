# MODEL — Inference, privacy and artifacts

## Preparation and inventory

Real interface: labels/scores/text/weights, available training, loader/versions, formats, artifacts and synthetic data. Define protection and adversarial access before testing.

## Walkthrough

1. Separate inference-time evasion, behavior extraction, memorization, membership and inversion.
2. Fix perturbation constraints or auxiliary knowledge and an appropriate baseline.
3. Use separate calibration/holdout and per-segment metrics with uncertainty.
4. For artifacts, check the digest/provenance and the effective loader without executing unknown content.
5. If execution needs to be demonstrated in the lab, use a controlled marker and trace; distinguish the carrier from the loading mechanism.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-027](../fieldcards/AI-027.md) | API and inference limits | TEST |
| [AI-031](../fieldcards/AI-031.md) | Model artifact integrity | TEST |
| [AI-032](../fieldcards/AI-032.md) | Insecure deserialization | TEST |
| [AI-037](../fieldcards/AI-037.md) | Privacy through memorization | TEST |
| [AI-038](../fieldcards/AI-038.md) | Membership inference | TEST |
| [AI-041](../fieldcards/AI-041.md) | Model behavior extraction | TEST |
| [AI-047](../fieldcards/AI-047.md) | Classifier evasion through rephrasing and benign additions | TEST |
| [AI-048](../fieldcards/AI-048.md) | Protected attribute inversion | TEST |
| [AI-030](../fieldcards/AI-030.md) | Training poisoning | TEST |
| [CFG-004](../fieldcards/CFG-004.md) | Loader, provenance and admission | CONFIG |

## Interpretation and limits

A surrogate model's fidelity does not demonstrate membership or data leakage. Hidden bits in tensors do not execute by themselves. A format rejection does not certify the whole loader.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
