# Merestone 0.3 — Operational playbook

This is the entry point for assessing an AI system. The unit of work is a case applied to an asset, actor, boundary and route. The catalog contains design reviews, configuration reviews, technical tests and scenarios; the plan is derived from verified capabilities.

## 0. How to use this guide together with the method

This guide is the entry point; the [full method](method/operations.md) defines the canonical ten-phase cycle (0–9). The sections of this page walk through that cycle as follows:

| Section of this guide | Method phases | Stage |
|---|---|---|
| 1. Prepare an assessment | 0 Prepare · 1 Understand · 2 Model threats | Prepare and understand |
| 2. Generate and review the plan | 4 Plan (freeze plan and protocols) | Model and plan |
| 3. Run activities — DESIGN/CONFIG | 3 Review design and configuration | Model and plan |
| 3. Run activities — TEST/REDTEAM | 5 Test components · 6 Run scenarios | Run |
| 4. Record and validate evidence | 5–7 (continuous recording) · 7 Validate | Run / Consolidate |
| 5. Consolidate, correct and retest | 7 Validate · 8 Report and remediate · 9 Retest and maintain | Consolidate and close |

Phase 3 (design and configuration review) can start before the plan is frozen with the available documentation, but its DESIGN/CONFIG tasks are part of the plan and are recorded and decided like the others. The phases allow going back: a test can reveal a new boundary and force a return to phase 1 with a plan revision. Terminology is fixed in the [glossary](method/glossary.md).

## 1. Prepare an assessment

1. Complete the [charter and templates](../templates/operational.md): objectives, dates, assets, identities, permissions, limits, contact, stop conditions, evidence and restoration.
2. Build the [inventory and threat model](architecture/inventory-and-threats.md). Use `present`, `absent` or `unknown` for each capability and provide evidence. A lack of access is not the absence of the component.
3. Consult the [full method](method/operations.md), especially baseline, result, evidence, severity and closure.
4. Choose modules by real capabilities: [LLM](modules/LLM.md), [RAG](modules/RAG.md), [tools](modules/TOOLS.md), [agents/memory](modules/AGENT.md), [MCP](modules/MCP.md), [consumers](modules/OUTPUT.md), [data](modules/ML-DATA.md), [models](modules/MODEL.md), [platform](modules/PLATFORM.md), [multimodal](modules/MULTIMODAL.md).

**Common core.** The reviews CORE-001…008 (DESIGN) and CFG-001/002 (CONFIG) do not depend on capabilities: they are generated on every route that declares DESIGN or CONFIG in `activity_types`. Including DESIGN on at least one route is mandatory (without it `check-plan` records `core_design_missing` and never returns 0 or 1); include CONFIG when there is deployed configuration. The CORE module also contains conditional CONFIG reviews (CFG-003…006) and cross-cutting cases activated by capability (AI-004, AI-050, AI-054, AI-061); see the [catalog](catalog.md).

It is not assumed that RAG includes tools, that an agent uses SQL or that MCP has an LLM in scope. The profile examples are inventory drafts, with unreviewed capabilities as UNKNOWN.

## 2. Generate and review the plan

From the framework folder, with Python 3.10 or later (the guided CLI `merestone.py` performs these steps with less typing; see the [README](../README.md)):

```console
python fieldguide.py init --profile rag --out runs/architecture.json
```

Complete that file with real assets and routes. Each route contains the asset, actor, boundary, access, scope, threats, capabilities and activities. Add routes for different tenants, tools, transports or consumers that change the hypothesis. Record evidence for every capability declared present or absent. Complete authorization, snapshot, limits and the inventory review. Add `test_protocols` for each case that will be run: variants, minimum trials per variant, design, rule and justification. Use [this template](../templates/test-protocol-v3.json). The absence of a protocol does not remove the obligation, but it prevents deciding it as PASS/FAIL.

```console
python fieldguide.py plan --architecture runs/architecture.json --out runs/plan.json
```

`runs/plan.json.manifest.json` is also created. Keep the approved manifest in a separate controlled location. The plan includes non-applicable and unknown obligations to explain their selection. The latter cannot become PASS. Deleting tasks, modifying assets or changing the catalog invalidates the plan.

For a readable guide with procedures and examples, use `--format md --out runs/plan.md`. The JSON is the verifiable record; the Markdown is a working view. Results from the JSON record are reported without inventing execution.

## 3. Run activities

**DESIGN:** compare requirements, architecture and responsibilities. Store documentary evidence and the decision. **CONFIG:** check the effective, current configuration. Both can conclude with verified deficiencies, without claiming exploitation.

**TEST:** run baseline, stimulus, reachability check, identity, decision and effect. Use the [fieldcards](catalog.md), their techniques and variants; record trials from [the template](../templates/trial-v3.json). The same technique can appear in several tasks because it is verified at different boundaries.

The [technique library](techniques.md) lets you locate mechanisms and their associated cases. The common activities are in the CORE fieldcards; before declaring a capability absent, resolve its reconnaissance in CORE-002 or record the uncertainty. An UNKNOWN task is not discarded for lack of access.

**REDTEAM:** select [scenarios](scenarios/README.md) by actor and objective. Add `REDTEAM` to the activities of the corresponding routes before freezing the plan. Do not add incompatible privileges between steps or treat an output simulation as an E2E exploitation.

Consult the [technique walkthroughs](walkthroughs/) for each technique. Record changes of language, task, data and recipient as an adaptation.

## 4. Record and validate evidence

Store files in the private store. Each record includes ID, relative path, SHA-256, size, collector, origin, classification, timestamp, redactions and kind. A decided technical test needs evidence of baseline, input, response, effect, identity and reachability. A review needs evidence of kind `review`; trials are not invented to complete it.

```console
python fieldguide.py check-plan runs/plan.json --manifest runs/plan.json.manifest.json --evidence-root private/evidence
python fieldguide.py report runs/plan.json --manifest runs/plan.json.manifest.json --evidence-root private/evidence --out runs/report.md
```

In a guided-CLI workspace the same check and report are `merestone status` and `merestone report`. For people who do not use the terminal, `merestone report --format html` writes a self-contained, read-only dashboard (`--layout document` for a top-to-bottom, print-friendly version); `--format both` writes Markdown and HTML together. `merestone ui` opens the same workflow as a local web interface (architecture editor, plan board, trial recording with drag-and-drop evidence and report export) that runs only on your computer.

In the UI, save route, readiness and protocol edits before freezing. Capability answers save immediately. Scope changes affect a frozen plan only after a revision; marking a route out of scope does not count as passing its tasks. See the [UI guide](../docs/UI-GUIDE.md) for the complete save, revision and evidence workflow.

Code 0: selected obligations resolved without FAIL and references verified. Code 1: there are FAILs and nothing pending. Code 2: missing readiness/evidence/verification, pending items/exclusions exist or the record is inconsistent. A code 0 does not certify the system: it depends on the scope, the frozen catalog and technical judgment. Without an external manifest or a verifiable store, no green closure is issued.

## 5. Consolidate, correct and retest

Use the [finding template](../templates/finding-v3.json) and the [tracking contract](method/findings-and-regression.md). Separate demonstrated impact, potential impact and confidence. Deduplicate by cause/correction, preserving routes; several control failures in a chain may require separate findings.

Retesting generates a new plan and new evidence; earlier results remain intact. Repeat the original, nearby variants, the benign operation and the full route. Risk acceptance keeps its owner, compensation and expiry, and is not presented as a correction.

## 6. Material and maintenance

- [Glossary and terminology conventions](method/glossary.md).
- [Content architecture and contributions](method/maintenance.md).
- [Execution, import and tool limitations](../docs/IMPLEMENTATION.md).
- [Versioned references](method/references.md).
- [Verification status](../docs/VERIFICATION.md).
