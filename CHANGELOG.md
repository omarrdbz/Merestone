# Changes

## 0.3.0 — 2026-10-01

First release of the operational AI security playbook.

- Canonical method with phases 0–9, a common core and ten modules (LLM, RAG, TOOLS, AGENT, MCP, OUTPUT, ML-DATA, MODEL, PLATFORM, MULTIMODAL).
- Catalog of 75 cases, 31 controls, 85 techniques, 129 Merestone-original example inputs and 6 scenarios by actor/objective.
- Capability-based selection and per-boundary tasks, with independent applicability, execution and result states, frozen test protocols and verifiable evidence.
- 15 technique walkthroughs, one per family, generated from the catalog.
- 114 versioned mappings to OWASP LLM 2026, MITRE ATLAS 2026.09, OWASP Agentic 2026, OWASP API 2023, NIST AI RMF 1.0, NIST AI 100-2 E2025 and MCP 2025-11-25, verified against the published sources on 2026-10-01.
- CLI (`fieldguide.py`), observation importer, plan revision and finding lifecycle (`governance.py`), and three instrumented local pilots.
- `check-plan` records the readiness gap `core_design_missing` when no route declares DESIGN.
