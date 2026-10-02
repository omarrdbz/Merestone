# Changes

## Unreleased

- `merestone report --format html|both [--open]`: self-contained, read-only HTML dashboard (`report_html.py`) to share with people who do not use the terminal: exit code with Mojo, readiness, coverage by module, task board by state with a details panel (protocol, trials, hashed evidence, fieldcard), search and module filter, light/dark and print styles; strict CSP and escaping, no external resources. `--layout document` gives a top-to-bottom, print-friendly alternative with a field of boundary stones per module.

- Guided CLI `merestone.py` (standard library only) over the unchanged engine: workspaces, guided inventory (`new --guided`), `status` with next steps, `caps`/`set`/`protocol` without JSON editing, readable task IDs (`CASE@ROUTE`), `record`/`decide`/`review` with automatic evidence hashing, `report`, `demo`, `doctor`.
- `merestone setup`: plain-language wizard for everything needed before planning; the pre-plan checklist now includes route access, actor and boundary, and `plan` refuses to freeze with blocking items unless `--anyway`.
- `pyproject.toml`: `python -m pip install -e .` installs the `merestone` command (editable; no dependencies). Launchers `merestone` (POSIX) and `merestone.cmd` (Windows) remain for use without installing.
- `merestone new` refuses to create workspaces inside the framework folder (they hold evidence); a missing-workspace error points to workspaces found in subfolders.
- Friendly errors with hints and typo suggestions.
- 27 CLI tests, including an assessment that reaches code 0 using only the guided CLI and tamper detection after recording.
- `playbook/start.md`: Python requirement aligned to 3.10+.

## 0.3.0 — 2026-10-01

First release of the operational AI security playbook.

- Canonical method with phases 0–9, a common core and ten modules (LLM, RAG, TOOLS, AGENT, MCP, OUTPUT, ML-DATA, MODEL, PLATFORM, MULTIMODAL).
- Catalog of 75 cases, 31 controls, 85 techniques, 129 Merestone-original example inputs and 6 scenarios by actor/objective.
- Capability-based selection and per-boundary tasks, with independent applicability, execution and result states, frozen test protocols and verifiable evidence.
- 15 technique walkthroughs, one per family, generated from the catalog.
- 114 versioned mappings to OWASP LLM 2026, MITRE ATLAS 2026.09, OWASP Agentic 2026, OWASP API 2023, NIST AI RMF 1.0, NIST AI 100-2 E2025 and MCP 2025-11-25, verified against the published sources on 2026-10-01.
- CLI (`fieldguide.py`), observation importer, plan revision and finding lifecycle (`governance.py`), and three instrumented local pilots.
- `check-plan` records the readiness gap `core_design_missing` when no route declares DESIGN.
