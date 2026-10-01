# CORE-003 — Threats and security requirements

Revision 1.0.0 · CORE · DESIGN

## Objective and risk

Each critical route has an actor, access, boundary, effect and expected control.
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

1. Define the protected business properties.
2. Model threats by actor and boundary using STRIDE and AI mechanisms.
3. Prioritize by privilege, exposure and impact; link cases and hypotheses.

## Techniques and examples


## Evidence

- Dated document/configuration/diagram
- Review reference and owner
- Decision and limitations per obligation

## Result

- FAIL: A threats and security requirements obligation is missing or contradicts the evidence.
- PASS: Each critical route has an actor, access, boundary, effect and expected control.
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
