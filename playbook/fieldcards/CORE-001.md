# CORE-001 — Scope and rules of engagement

Revision 1.0.0 · CORE · DESIGN

## Objective and risk

Authorized assets, dates, identities, actions, limits, contact, evidence and restoration.
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

1. Enumerate allowed/excluded objectives and effects.
2. Verify who can authorize the scope and validity.
3. Fix budgets, stop conditions, custody and restoration before testing.

## Techniques and examples


## Evidence

- Dated document/configuration/diagram
- Review reference and owner
- Decision and limitations per obligation

## Result

- FAIL: A scope and rules-of-engagement obligation is missing or contradicts the evidence.
- PASS: Authorized assets, dates, identities, actions, limits, contact, evidence and restoration.
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

- NIST AI RMF 1.0 GOVERN: related_to. Owners and rules of engagement.

Limits: Do not extrapolate the result to untested versions or routes.

Independent review: pending. The fieldcard does not imply execution against a real system.
