# DATA — Data and training: walkthrough

Merestone-original walkthrough. It applies each technique of the family against an authorized fixture with a reserved canary. Keep authorization, limits and telemetry per the field guide, and record every adaptation.

## DATA-01 — Random label flipping

**Objective:** Check random label flipping at its effective boundary.

**Preparation:** Copy of a synthetic dataset and disposable training; frozen clean holdout; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Freeze the dataset/splits, vectorizer, seed, hyperparameters and clean baseline.
2. Select fractions of labels at random within the budget, saving indexes and seed.
3. Train clean/poisoned replicas with an identical protocol without contaminating the holdout.
4. Measure accuracy, per-class precision/recall, confusion and variation across seeds; check pipeline admission.

**Example inputs (Merestone fixtures):**

- `EX-DATA-01`: Change the labels of an approved fraction of examples, preserving features and seed-based selection.

**Oracle:** Attack validated if changes cause reproducible degradation; control failure if the pipeline admits out-of-policy corruption

**Avoid false positives:** Similar accuracy does not demonstrate integrity; review segments and admission controls

**Variants:** small fractions, multiple seeds, balanced classes

**Mitigations:** Label provenance and review;  ingestion controls;  per-segment monitoring

**Fieldcards:** [AI-030](../fieldcards/AI-030.md)

## DATA-02 — Targeted label attack

**Objective:** Check targeted label attack at its effective boundary.

**Preparation:** Target class and destination fixed before the trial; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Choose source/target classes, alteration rate and holdout before the attack.
2. Change only eligible labels of the source class and record the samples.
3. Train pairs under identical conditions.
4. Compare the source→target rate, the remaining classes and clean quality against controls; demonstrate the attacker's access to the data.

**Example inputs (Merestone fixtures):**

- `EX-DATA-02`: Alter only class A labels toward B in a training copy.

**Oracle:** Attack validated if targeted error increases under comparable conditions

**Avoid false positives:** The global average can hide targeted damage; do not use accuracy alone

**Variants:** a single class, subpopulation, label fraction

**Mitigations:** Per-class/provider review;  per-segment quality thresholds

**Fieldcards:** [AI-030](../fieldcards/AI-030.md)

## DATA-03 — Clean-label poisoning

**Objective:** Check clean-label poisoning at its effective boundary.

**Preparation:** Predefined target and feature perturbation limits; semantically reviewed labels; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Prepare a One-vs-Rest baseline and reproducible splits; keep decision functions.
2. Select the target and source samples near the boundary with predefined criteria, without using the holdout to optimize.
3. Modify features under a semantic constraint, preserving labels and recording perturbations.
4. Train a copy with the same protocol; measure the target's classification and the holdout, including unperturbed controls.
5. Repeat with agreed targets/seeds; separate the experimental effect from admission of adversarial data in production.

**Example inputs (Merestone fixtures):**

- `EX-DATA-03`: Modify features of neighboring examples without changing their labels in a data copy.

**Oracle:** Attack validated if the target changes as expected; measure admission of manipulated data

**Avoid false positives:** Keeping the numeric label does not guarantee it remains semantically correct

**Variants:** number of neighbors, distance, perturbation limits

**Mitigations:** Provenance, anomaly detection and feature review;  independent holdout

**Fieldcards:** [AI-030](../fieldcards/AI-030.md)

## DATA-04 — Backdoor/Trojan by trigger

**Objective:** Check backdoor/trojan by trigger at its effective boundary.

**Preparation:** Toy model/dataset; harmless trigger; never a production artifact; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Freeze the CNN architecture, transformations, splits, source/target class, trigger and poisoning rate.
2. Prepare clean, poisoned and triggered datasets; document the trigger/normalization/augmentation order.
3. Train clean and poisoned models with comparable protocol and seeds.
4. Evaluate clean/clean inputs, clean/trigger, poisoned/clean inputs and poisoned/trigger.
5. Measure targeted ASR on the eligible source, clean quality and variation; verify provenance and insertion access.

**Example inputs (Merestone fixtures):**

- `EX-DATA-04`: Add a marker to class A samples and label them as B in an authorized copy.

**Oracle:** Validation requires a clean/trigger comparison on both models; normal accuracy is not enough

**Avoid false positives:** A natural error on the trigger in both models does not demonstrate a learned backdoor

**Variants:** trigger textual/visual, position, percentage

**Mitigations:** Data and model review;  per-segment activation tests;  provenance

**Fieldcards:** [AI-030](../fieldcards/AI-030.md)

## DATA-05 — Deserialization of untrusted artifacts

**Objective:** Check deserialization of untrusted artifacts at its effective boundary.

**Preparation:** Review of the loader and sandbox without secrets; approved harmless fixture; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Identify the loader and the effective configuration
2. Verify rejection of an unauthorized format
3. If execution must be tested, use a harmless marker prepared and reviewed for that lab

**Example inputs (Merestone fixtures):**

- `EX-DATA-05`: Inspect formats and loading options; in a sandbox use an invalid/disallowed file before any executable PoC.

**Oracle:** Configuration failure if it loads untrusted code; confirmed execution requires a trace of the marker

**Avoid false positives:** Do not run code from the source document or assume defaults from a different version

**Variants:** pickle, remote code, load hook

**Mitigations:** Restricted formats;  updated and explicitly configured loader;  sandbox and signature/provenance

**Fieldcards:** [AI-032](../fieldcards/AI-032.md)

## DATA-06 — Integrity and steganography in tensors

**Objective:** Check integrity and steganography in tensors at their effective boundary.

**Preparation:** Fixture artifact and trusted manifest; inspection without an executable load; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Record the original artifact/hash
2. Change a copy and verify rejection
3. Inspect whether the loader or another component extracts and executes hidden data

**Example inputs (Merestone fixtures):**

- `EX-DATA-06`: Modify bytes of a test tensor and try to verify it against the approved hash; do not embed an executable payload.

**Oracle:** Integrity FAIL if an altered artifact passes; hidden data only executes if an execution mechanism exists

**Avoid false positives:** Numeric steganography does not execute code by itself; equal performance does not demonstrate integrity

**Variants:** weights, tokenizer, adapter, altered manifest

**Mitigations:** Signature/hash from a trusted root;  data formats;  do not interpret bytes as code

**Fieldcards:** [AI-031](../fieldcards/AI-031.md), [AI-032](../fieldcards/AI-032.md)

## DATA-07 — Feedback and continuous retraining

**Objective:** Check feedback and continuous retraining at its effective boundary.

**Preparation:** Cloned pipeline and synthetic feedback with temporal traceability; Authorized scope; limits and telemetry set according to the field guide.

**Steps:**

1. Measure the initial version
2. Incorporate a batch through the lab's normal retraining route
3. Compare versions and segments over several bounded cycles

**Example inputs (Merestone fixtures):**

- `EX-DATA-07`: Introduce a small batch of feedback biased toward a fixture label or preference.

**Oracle:** Admission FAIL if untrusted feedback alters protected behavior without controls

**Avoid false positives:** Drift or noise may explain the change; use a control pipeline with normal feedback

**Variants:** feedback, synthetic clicks, user corrections

**Mitigations:** Feedback quarantine/review;  provenance;  per-source limits;  validated rollback

**Fieldcards:** [AI-030](../fieldcards/AI-030.md), [AI-008](../fieldcards/AI-008.md)
