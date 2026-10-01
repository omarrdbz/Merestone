# Operational templates

Copy these templates to the assessment's private space. Fields in brackets are completed before approving the phase; do not use invented values. The 3.0 schemas and the tracking rules accompany these templates; assignment to a ticket manager is external.

## A. Scope and authorization charter

- Assessment ID / system / owner / business owner: [complete]
- Security objectives and protected business processes: [complete]
- Exact authorized environment and resources (URLs, repos, namespaces, models, tenants): [complete]
- Assessment window and time zone: [start/end]
- Identities, roles and test accounts: [complete]
- Allowed activities: [read, modify fixtures, index, run tools, train a copy]
- Exclusions and third-party systems: [complete]
- Allowed data and canaries; handling of unexpected data: [complete]
- Limits: [requests, tokens, cost, concurrency, time, size, agent steps]
- Telemetry and stop criteria: [complete]
- Operational and incident contact / channel: [complete]
- Restoration and subsequent validation: [owner and procedure]
- Evidence: [private repository, access, retention, deletion]
- Approvers / authority / date / authorization reference: [complete]

## B. Inventory and flow

| Asset ID | Component/version | Owner | Data | Identity | Permissions | Dependencies | Verification source |
|---|---|---|---|---|---|---|---|
| [A-001] | [complete] | | | | | | |

| Flow ID | Origin → destination | Boundary | Transformations | Authorization | Logs/correlation | Persistence/egress |
|---|---|---|---|---|---|---|
| [F-001] | [complete] | | | | | |

Attach a diagram, a tools/MCP inventory and an AIBOM: component, version/digest, provider, provenance, license, signature, location, dependency, owner, review status. The AIBOM must include models, adapters, tokenizers, datasets, embeddings and versioned prompts, in addition to packages.

## C. Threat and test plan

- Threat ID: [TH-001]
- Actor / initial access / objective / asset: [complete]
- Preconditions and route between components: [complete]
- Falsifiable hypothesis and observable effect: [complete]
- Expected controls / initial risk: [complete]

| Case/review | Asset | Applicability/reason | Variant/fixture | Oracle | Trials | Budget | Owner |
|---|---|---|---|---|---|---|---|
| [AI-xxx] | | | | | | | |

The selection includes a benign baseline and cleanup. Record exclusions with approver and date. For statistical tests, state the hypothesis, threshold, sample size, controls and criterion before observing results.

## D. Execution and evidence record

- Run ID / assessment ID / case-review / variant / assessor / UTC timestamp: [complete]
- Snapshot: [app, model, prompt hash, corpus/index, tools, permissions, defenses and parameters]
- Initial state / fixture / user-tenant / request ID: [complete]
- Exact input / observed events / response / final effect: [private references]
- Working benign baseline / complete trace: [yes/no + evidence]
- Task applicability: [APPLICABLE/NOT_APPLICABLE/UNKNOWN]; scope and access: [complete separately]
- Execution: [NOT_RUN/BLOCKED/ERROR/COMPLETED]
- Technical result: [empty/PASS/FAIL/INCONCLUSIVE]; only COMPLETED admits a result
- Frozen protocol: [required variants, minimum valid trials per variant, design, rule and justification]
- Attack successes / valid trials / excluded and reason: [complete]
- Cleanup and verification / deviations: [complete]

| Evidence ID | Run ID | UTC | Collector | Origin | Classification | Private URI | SHA-256 | Size | Redaction |
|---|---|---|---|---|---|---|---|---|---|
| [E-001] | | | | | | | | | |

## E. Finding

- ID / specific title / state: [complete]
- Summary: [actor and action that crossed a boundary; asset and effect]
- Asset / threat / cases-reviews / controls / runs / evidence: [IDs]
- Versions and reproduction conditions: [complete]
- Minimal procedure: [steps and fixtures, without real data in a public copy]
- Expected vs. observed: [complete]
- Proven impact / possible impact not yet proven: [separate]
- I [1–5] and justification / F [1–5] and justification / I×F / severity: [complete]
- Confidence and limits: [complete]
- Root cause and affected routes: [complete]
- Mappings: [framework, version, ID, relation type, justification, URL]
- Immediate mitigation / structural correction / compensating control: [complete]
- Owner / ticket / target date / acceptance criterion: [complete]
- Immutable history: [date, actor, previous/new state, reason]
- Retest / residual risk / closure approver: [complete]

## F. Retest and acceptance

| Finding | Change/version | Original run | New run | Original and variants | Baseline | Remaining coverage | Decision/reviewer |
|---|---|---|---|---|---|---|---|
| [FND-001] | | | | | | | |

If risk is accepted: authorized business owner, reason, accepted assets and effects, verified compensations, expiry and triggers for early review. On expiry, return to triage; do not close as corrected.

## G. Assessment report

1. Executive summary: system, impact, main causes, required decisions.
2. Authorized scope, dates, method, access and limitations.
3. Architecture/boundaries, versions and coverage: applicable, run, excluded and pending.
4. Prioritized findings with references to evidence and versioned mappings.
5. Remediation: owner, deadline, dependencies and compensations.
6. Retest, residual risks, added regressions and next review.
7. Private evidence annex and custody record; public annex synthetic only.

## H. Mapping to the 3.0 record

Use `architecture-v3.schema.json`, `plan-v3.schema.json`, `trial-v3.schema.json`, `evidence-v3.schema.json` and `finding-v3.schema.json`. The empty JSON models are forms; they are not evidence or complete records.

Record task_id, case_id/revision, asset_id, route_id, boundary, actor, threat_ids and control_ids. For a trial: example_id, technique, variants, exact adaptation, snapshot, parameters, reachability, identity, baseline, expected/observed and evidence. For a review: current configuration/document, criterion and reviewer. Keep applicability, execution and result separate.

In the inventory, document the evidence for present and absent capabilities, unknowns, provider responsibilities and the assessor's access. Profiles are initialization aids; they do not authorize tests or prove that components exist.
