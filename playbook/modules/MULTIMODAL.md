# MULTIMODAL — Image, audio, video and transformations

## Preparation and inventory

Supported modalities and their parsers/transcribers/OCR, the resulting context and consumers. Prepare semantically equivalent pairs with ground truth and canaries.

## Walkthrough

1. Measure extraction and the benign task per modality.
2. Change one modality/channel per trial: visual instructions, audio, metadata or frame.
3. Check the intermediate representation, arrival in the context and provenance.
4. Compare with the text version and measure decision, call and final effect.
5. Restore files/indexes and report modalities not tested due to lack of support/access.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-052](../fieldcards/AI-052.md) | Instructions in multimodal inputs | TEST |

## Interpretation and limits

A failed transcription does not demonstrate a defense. An attack in an image requires observing the channel actually used, not assuming OCR is the only route. Do not extrapolate text results to audio/video.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
