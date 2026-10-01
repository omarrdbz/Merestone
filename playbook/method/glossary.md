# Glossary and terminology conventions

## Convention

- Identifiers are kept exactly as they appear in schemas, catalogs and the CLI (states, activities, capabilities, JSON fields): `APPLICABLE`, `TEST`, `retrieval`, `reachability`.
- Use the terms in this table consistently in all documents.
- If a document uses a variant different from this table, this table prevails.

## Terms

| Merestone term | Field / identifier | Operational definition |
|---|---|---|
| Route | `routes[]` | Complete path origin → transformation → context → decision → tool → resource → effect, with a concrete actor, identity and boundary. Unit of assessment. |
| Trust boundary | `boundary` | Point where the trust level or authority changes: user/service, tenants, document/instruction, model/executor, agent/server, internal network/Internet, build/production. |
| Asset | `assets[]` | Component, data or business capability being protected. |
| Actor | `actor` | Who attempts the effect, with their initial access. |
| Capability | `capabilities` | Function the system has on a route (`present`, `absent`, `unknown`). `present`/`absent` require evidence; anything not reviewed stays `unknown`. |
| Case · fieldcard | `cases` | Verification of a control at a boundary, documented in a fieldcard with applicability, procedure, oracle and evidence. |
| Control (expected) | `CTL-*` | Invariant that should prevent the harm; the case oracle evaluates it. |
| Technique | `techniques` | Reusable stimulus mechanism. Relating it to a case is not the same as running a test. |
| Example | `examples` | Concrete Merestone-original fixture input; every adaptation is recorded. |
| Scenario | `SCN-*` | Chain of steps by actor and objective; activated with `REDTEAM`. |
| Task · obligation | `tasks` | Case applied to asset × route × actor × boundary × activity within a plan. |
| Activity | `activity` | `DESIGN` (documentary review), `CONFIG` (effective configuration), `TEST` (technical test at a boundary), `REDTEAM` (chained scenario). |
| Common core | CORE | Reviews CORE-001…008 and CFG-001/002, without a capability condition; they require DESIGN/CONFIG on the route. |
| Applicability | `applicability` | `APPLICABLE`, `NOT_APPLICABLE` (required capability absent, with evidence) or `UNKNOWN` (depends on something unknown; never becomes PASS or not applicable). |
| Execution | `execution` | `NOT_RUN`, `BLOCKED`, `ERROR`, `COMPLETED`. |
| Result | `result` | `PASS`, `FAIL`, `INCONCLUSIVE`; only with `COMPLETED`. Only `PASS` counts as demonstrated protection. |
| Exclusion | `exclusion` | Obligation accepted outside execution with reason, approver, expiry and residual risk; it does not increase decided coverage. |
| Baseline (benign) | `baseline` | Equivalent legitimate operation that must work before and after the test. |
| Restricted control | — | Same action without an adversarial technique on an unauthorized resource; it must be rejected. |
| Stimulus · variant | `input` · `variant` | Adversarial input; each variant changes a single condition. |
| Reachability | `reachability` | Proof that the stimulus reached the evaluated component (context, dispatcher, parser…). |
| Effective identity | `identity` | Principal with which the component actually acted, not the one declared in text. |
| Effect | `effect` | Final state observed in the resource; it decides the result. |
| Oracle | `oracle` | Case rule that decides FAIL/PASS/INCONCLUSIVE from the observable effect. |
| Canary | — | Unique marker per trial used to demonstrate a leak or reachability without real data. |
| Snapshot | `snapshot_ref` | Versions of app, model, prompts, corpus/index, tools, permissions, defenses and parameters. |
| Test protocol | `test_protocols` | Variants, minimum trials per variant, design, decision rule and justification, fixed before measuring. |
| Trial | `trials` | One run of one variant. |
| Frozen plan · manifest | `plan.json` · manifest | Plan whose obligations and catalog are fixed by hash; the approved manifest is stored outside the plan. |
| Evidence | `evidence` | File with ID, SHA-256, size, collector, origin, classification, timestamp and redactions. The hash detects changes; it does not prove authorship. |
| Finding | `finding` | Confirmed failure grouped by root cause and correction, with affected routes, I×F and confidence. |
| Observation | — | Anomalous behavior without demonstrated impact; not a finding. |
| I×F | impact × feasibility | Local prioritization 1–5 × 1–5: 1–4 low, 5–9 medium, 10–16 high, 17–25 critical. Not CVSS. |
| Confidence | `confidence` | High, medium or low according to effect and reproduction; reported separately from risk. |
| Attack success rate (ASR) | — | Trials with a violation / valid trials of the same variant and snapshot. |
| Retest · regression | — | New plan with original, neighbors, benign and full route; suite repeated on change triggers. |
| Exit code | `exit_code` | 0 complete without FAIL and verified; 1 complete with FAIL; 2 incomplete, unverified or with readiness gaps. |
