# CORE-005 — Data, persistence and retention

Revision 1.0.0 · CORE · DESIGN

## Objective and risk

Each data item has a classification, readers, destinations and lifecycle.
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

1. Record collection, context, logs, memory, backups and third parties.
2. Verify the purpose and access of each copy.
3. Fix deletion/revocation and evidence of compliance per route.

## Techniques and examples


## Evidence

- Dated document/configuration/diagram
- Review reference and owner
- Decision and limitations per obligation

## Result

- FAIL: A data, persistence and retention obligation is missing or contradicts the evidence.
- PASS: Each data item has a classification, readers, destinations and lifecycle.
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
