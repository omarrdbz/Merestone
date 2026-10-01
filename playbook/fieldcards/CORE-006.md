# CORE-006 — Provenance and changes

Revision 1.0.0 · CORE · DESIGN

## Objective and risk

Artifacts and dependencies have documented origin, review and admission.
Incomplete assessment or one without verifiable support.

Controls: CTL-GOVERNANCE

## Applicability

One alternative must be satisfied: common core

Actor: Assessor and system owners

Access: gray-box; access limitations are recorded without inferring PASS

## Preparation

- Owner and documentation/configuration accessible; known limits.

Allowed baseline: No attack applies; compare claims with documents and configuration.

Restricted control: Record inconsistencies and owners.

## Procedure

1. Create an AIBOM with versions/digests and owners.
2. Identify the update and revocation path.
3. Select admission and rollback cases for existing components.

## Techniques and examples


## Evidence

- Dated document/configuration/diagram
- Review reference and owner
- Decision and limitations per obligation

## Result

- FAIL: A provenance and change obligation is missing or contradicts the evidence.
- PASS: Artifacts and dependencies have documented origin, review and admission.
- INCONCLUSIVE: Documents or owners not available.

## Variants and metrics

Routes and roles present.
{"unit": "documentary obligation", "sample_plan": "Full scope review", "denominator": "Applicable obligations"}

## Stop, cleanup and retest

Approved limit reached; Unexpected effect outside the fixture; Lost observability
There are no technical effects; close temporary review access.
- Original and nearby variant
- Benign baseline
- Boundary and complete route
- Verify restoration

## Recommendations

- Resolve discrepancies with the owner and update the inventory/plan.

## References


Limits: Do not extrapolate the result to untested versions or routes.

Independent review: pending. The fieldcard does not imply execution against a real system.
