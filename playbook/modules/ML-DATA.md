# ML-DATA — Data, training and poisoning

## Preparation and inventory

Dataset/provenance, splits, untouchable holdout, architecture, transformations, hyperparameters, seeds and poisoning budget. Record the adversary's access to the pipeline.

## Walkthrough

1. Measure a clean baseline and fix the hypothesis/metric before building the poisoning.
2. Run complete label flipping, targeted, clean-label or trigger protocols according to the threat.
3. Keep sample indexes, perturbations, labels and the order of transformations.
4. Evaluate clean quality and per-class/target damage; for triggers use the four combinations clean/poisoned and without/with trigger.
5. Repeat under comparable conditions and separate the experimental effect from an admission failure; restore versions.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-030](../fieldcards/AI-030.md) | Training poisoning | TEST |

## Interpretation and limits

Global accuracy can hide targeted damage. Clean-label must preserve the label's meaning, not just its stored value. Evaluation data are not used to optimize the attack reported as holdout.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
