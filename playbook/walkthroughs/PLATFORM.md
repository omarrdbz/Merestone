# PLATFORM — Platform and supply chain: walkthrough

This walkthrough applies each technique of the family against an authorized fixture with a reserved canary. Keep authorization, limits and telemetry per the field guide, and record every adaptation.

## API-01 — API properties and role

**Objective:** Verify the security control at untrusted JSON → data model.

**Preparation:** Current authorization, isolated environment, synthetic data and approved limits.; Fixture API with immutable role/tenant fields

**Steps:**

1. Freeze the snapshot and run the benign operation with evidence.
2. Create resource A with editable and immutable fields and confirm the allowed edit.
3. Separately add role, tenant and owner to the update body.
4. Repeat through the tool/chatbot if it exists; verify the identity derived from the token.
5. Read the resource with a new session and compare field persistence, not just the HTTP response.
6. Restore fixtures and confirm the final state.

**Example inputs (Merestone fixtures):**

- `EX-API-01`: Fixture request: change display_name and insert tenant=B without permission.

**Oracle:** The server persists fields that should not be modifiable

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** anidados, patch, batch

**Mitigations:** Per-role field allowlist; Separate DTOs and server-side policy

**Fieldcards:** [AI-026](../fieldcards/AI-026.md)

## T-AI-053 — Detection of and response to boundary violations

**Objective:** Verify detection of and response to boundary violations.

**Preparation:** Agreed test alert, canary and response contact; isolated environment; Current charter, limits and telemetry defined.

**Steps:**

1. Freeze versions, state and policy; run the allowed baseline.
2. Generate a benign event and confirm correlation.
3. Emit a controlled fixture violation and measure alerting, triage and access to evidence.
4. Exercise revocation of the fixture capability/credential and restoration; verify the reduction of the effect.
5. Keep traces, restore fixtures and check queues/residual state.

**Example inputs (Merestone fixtures):**

- `EX-T-AI-053`: Generate a benign event and confirm correlation.

**Oracle:** The critical event is not detected/correlated or cannot be contained according to the agreed objective.

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** leak, improper action, consumption

**Mitigations:** Correlated telemetry; Response playbook; Exercise revocation and restoration

**Fieldcards:** [AI-053](../fieldcards/AI-053.md)

## T-AI-057 — Integrity of adapters, tokenizer and embeddings

**Objective:** Verify the integrity of adapters, tokenizer and embeddings.

**Preparation:** AIBOM with model components; benign original and altered artifacts; trusted manifest; Current charter, limits and telemetry defined.

**Steps:**

1. Freeze versions, state and policy; run the allowed baseline.
2. Inventory the weights, adapters, tokenizer, templates, embeddings/reranker and plugins used.
3. Change a fixture dependency while keeping the visible name.
4. Attempt admission and rollback; observe digest, provenance and approval verification.
5. Keep traces, restore fixtures and check queues/residual state.

**Example inputs (Merestone fixtures):**

- `EX-T-AI-057`: Inventory the weights, adapters, tokenizer, templates, embeddings/reranker and plugins used.

**Oracle:** An unapproved or revoked component is admitted by trusting only its name.

**Avoid false positives:** Verify baseline, identity and effect; do not attribute success to generated text alone.

**Variants:** adapter, tokenizer, embedding, plugin

**Mitigations:** Pinning by digest and provenance; Change review; Regression of dependent components

**Fieldcards:** [AI-057](../fieldcards/AI-057.md)
