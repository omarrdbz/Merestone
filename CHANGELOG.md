# Changes

## Unreleased

- Route editor (“Flow you will assess”): a route is explained as who starts the action, the components it passes through and its result; an illustrative example loads only on request and never touches capabilities; separate fields for the actor's permissions and the assessor's access; trust boundaries are marked explicitly per step (permissions, identity, authority, data trust) instead of drawing every connection as one; the relation between route fields and the plan is explained beside the editor; an engine-calculated **Effect on the plan** shows saved values next to unsaved activities with example tasks; routes can be added, and removed while not in the frozen plan; a route saves in one atomic write with clear unsaved/saving/error/saved states and a revision summary that says where earlier results stay. Tasks explain why they are in the plan from the frozen route. New `merestone route` command and `set permissions|check`. Optional route fields `actor_permissions` and `trust_boundaries` in the architecture and plan schemas; obligations and existing plans are unchanged. Opening a test task no longer creates a phantom unsaved protocol. See the [route editor audit](docs/UX-AUDIT.md#route-editor-second-pass) and the [UI guide](docs/UI-GUIDE.md). Validation: 91 Python tests and 29 client tests.
- UI audit: readable scope and reachability labels, accurate save guidance, unsaved-architecture freeze guard, duplicate-submission guard, evidence-upload race fixes, filtered task counts, keyboard/focus improvements, responsive capability columns and corrected theme colors. The welcome screen suggests a workspace outside the framework. See [audit results](docs/UX-AUDIT.md) and the [UI guide](docs/UI-GUIDE.md). Validation: 83 Python tests and 13 client tests.

- Cleaner visual design shared by the web interface, both HTML report layouts and the explainer page: white surfaces, hairline rules, a single accent color and status shown as a small dot. The interface now has a sidebar (navigation, pending list, exit code), the plan as a filterable list grouped by state and a detail pane beside it; the report board lists tasks grouped by state instead of columns. Behavior and checks are unchanged.
- Fieldcards and walkthroughs no longer repeat a provenance disclaimer under every technique (rendering only; the catalog and its hash are unchanged, so existing plans stay valid).
- `merestone ui`: local web interface (`ui_server.py`, `ui/app.html`; standard library only, 127.0.0.1, no network). Architecture editor with the route drawn as boundary stones, readiness fields, capabilities as switches or a 16-question interview, test protocols, freeze and revision; plan board by state with fieldcards; trial, decision and review forms with drag-and-drop evidence hashed in the browser and re-hashed on arrival; always-visible status light and pending list (with optional terminal equivalents); report export in either layout; activity log; light and dark themes; keyboard shortcuts. Every write goes through the CLI command functions. Session key and strict cookie, Host and Origin checks, custom API header, nonce-based CSP. 10 tests.
- `merestone report --format html|both [--open]`: self-contained, read-only HTML dashboard (`report_html.py`) to share with people who do not use the terminal: exit code and its meaning, readiness, coverage by module, task board by state with a details panel (protocol, trials, hashed evidence, fieldcard), search and module filter, light/dark and print styles; strict CSP and escaping, no external resources. `--layout document` gives a top-to-bottom, print-friendly alternative with a field of boundary stones per module.

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
