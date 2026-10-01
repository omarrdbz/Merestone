# CORE-002 — Cross-checked architecture and inventory

Revision 1.0.0 · CORE · DESIGN

## Objective and risk

Observable assets, flows, capabilities and boundaries with owners.
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

1. Inventory versions, data, identities and dependencies.
2. Compare the diagram with configuration or traces for each route.
3. Record unknown capabilities and third-party access; do not infer absences.

## Techniques and examples


## Evidence

- Dated document/configuration/diagram
- Review reference and owner
- Decision and limitations per obligation

## Result

- FAIL: A verified architecture and inventory obligation is missing or contradicts the evidence.
- PASS: Observable assets, flows, capabilities and boundaries with owners.
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

- NIST AI RMF 1.0 MAP: related_to. System context and boundaries.

Limits: Do not extrapolate the result to untested versions or routes.

Independent review: pending. The fieldcard does not imply execution against a real system.
