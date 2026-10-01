# Findings, risk and regression

## Validation and consolidation

Separate design deficiencies, configuration deficiencies, technical vulnerabilities and out-of-policy behavior. A textual claim does not prove access, execution or sending. The evidence must identify the boundary, principal, resource and effect according to the case. The leak of a protected canary can be demonstrated in the text channel; a canary introduced by the attacker is an echo.

Consolidate by cause and verifiable correction, keeping all routes and effects. Do not group independent injection, authorization and egress failures just because they appear in the same chain. Keep false positives and duplicates with their reason and references.

## Risk and confidence

Keep I×F (1–5 per axis) as a local prioritization: 1–4 low, 5–9 medium, 10–16 high and 17–25 critical. Justify impact, access, exposure, complexity and feasibility. Prioritize reviewing systemic impact even if its feasibility is low. Do not convert the result to CVSS or use ASR as a substitute for feasibility.

High confidence requires a supported effect and reproduction; medium can reflect a single effect or partial traces; low describes a pending indication. In statistical tests, record the hypothesis, population, adversary knowledge, baseline, sample size and uncertainty. Separate adaptive exploration from a fixed test and keep failed attempts.

## History and closure

Sequence: proposed → confirmed → assigned → in remediation → ready for retest → closed. Alternatives: duplicate, false positive or accepted risk. Do not overwrite earlier results. Every transition carries a date, actor, previous/new state and reason.

Closing as corrected requires an owner, a corrected version, a new plan, original/neighbor/benign evidence, an effective control and a reviewer. High/critical findings require a reviewer different from the implementer. The tool can validate references, dates and states; it cannot replace that human independence.

Accepting a risk requires business authority, scope, reason, verified compensation and expiry. On expiry it returns to triage. A plan can be administratively closed with accepted pending items, but its technical coverage continues to show exclusions and uncertainty.

## Operational report

1. Summary of the system, impact and required decisions.
2. Scope, version, owners, authorizations, access and third parties.
3. Architecture, boundaries and verified/unknown assumptions.
4. Coverage by asset/boundary and DESIGN/CONFIG/TEST/REDTEAM: applicable, unknown, excluded and decided.
5. Findings with expected/observed, cause, minimal reproduction, evidence, proven/potential impact, risk and confidence.
6. Corrections, containment, owners, dates and acceptance criteria.
7. Retest and residual risk; evidence and traceability annexes.

The number of catalog examples is an editorial figure, not a measure of system security.

## Regression triggers

| Change | Retest at least |
|---|---|
| Model/prompts | Injection, context, policies, output and critical routes |
| Corpus/chunking/embedding/reranker | Retrieval, ACL, ranking, provenance, revocation |
| Tools/permissions | Dispatcher, authorization, intent/approval, egress and effects |
| Memory/delegation/queues | Scope, persistence, identity, idempotency and cancellation |
| MCP/transport/servers | Trust, version/capabilities, tokens/sessions or local process as appropriate |
| Loaders/dependencies/deploy | Integrity, provenance, isolation, admission and rollback |
| Guardrails/evaluator | Calibration, failure, route bypass, streaming and false refusals |

Keep finding IDs and append new plans. Changes to the oracle, policy, adapter or catalog may prevent direct comparisons; explain what changed and establish a new baseline.
