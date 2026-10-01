# Operational catalog

View generated from `catalog/cases/index.json`.

## How to read the CORE module

The CORE module groups three kinds of fieldcards: (1) unconditional common-core reviews, CORE-001…008 (DESIGN) and CFG-001/002 (CONFIG); (2) CONFIG reviews conditioned by capability, CFG-003…006; and (3) cross-cutting cases that do not belong to a single module, AI-004, AI-050, AI-054 and AI-061, activated by capability. Unconditional reviews are only generated on routes that declare DESIGN or CONFIG in `activity_types`; `check-plan` records the gap `core_design_missing` and does not issue code 0 or 1 if no route declares DESIGN. Declare CONFIG when there is deployed configuration to review.

Numbering: AI-060 is retired (it was reserved during construction and dropped to avoid duplicating AI-038). It is not reused.

| Case | Module | Activity | Controls |
|---|---|---|---|
| [AI-001 — Direct injection](fieldcards/AI-001.md) | LLM | TEST | CTL-CONTEXT |
| [AI-002 — Indirect injection in RAG](fieldcards/AI-002.md) | RAG | TEST | CTL-CONTEXT |
| [AI-003 — Exposure of protected context](fieldcards/AI-003.md) | LLM | TEST | CTL-CONFIDENTIALITY |
| [AI-004 — Cross-session and cache leakage](fieldcards/AI-004.md) | CORE | TEST | CTL-ISOLATION |
| [AI-005 — Contaminated persistent memory](fieldcards/AI-005.md) | AGENT | TEST | CTL-MEMORY |
| [AI-006 — RAG retrieval ACL](fieldcards/AI-006.md) | RAG | TEST | CTL-AUTHORIZATION |
| [AI-007 — Knowledge revocation and deletion](fieldcards/AI-007.md) | RAG | TEST | CTL-REVOCATION |
| [AI-008 — Poisoning of a retrievable source](fieldcards/AI-008.md) | RAG | TEST | CTL-PROVENANCE |
| [AI-009 — Ranking saturation](fieldcards/AI-009.md) | RAG | TEST | CTL-RETRIEVAL |
| [AI-010 — Unsupported citations and responses](fieldcards/AI-010.md) | LLM | TEST | CTL-GROUNDING |
| [AI-011 — Output to HTML](fieldcards/AI-011.md) | OUTPUT | TEST | CTL-OUTPUT |
| [AI-012 — Output to SQL](fieldcards/AI-012.md) | OUTPUT | TEST | CTL-OUTPUT |
| [AI-013 — Output to a code executor](fieldcards/AI-013.md) | OUTPUT | TEST | CTL-EXECUTION |
| [AI-014 — Action without approval](fieldcards/AI-014.md) | TOOLS | TEST | CTL-INTENT |
| [AI-015 — Excessive tool privileges](fieldcards/AI-015.md) | TOOLS | TEST | CTL-AUTHORIZATION |
| [AI-016 — Agent resources and loops](fieldcards/AI-016.md) | AGENT | TEST | CTL-BUDGET |
| [AI-017 — Retry and idempotency](fieldcards/AI-017.md) | AGENT | TEST | CTL-IDEMPOTENCY |
| [AI-018 — Delegation between agents](fieldcards/AI-018.md) | AGENT | TEST | CTL-DELEGATION |
| [AI-019 — Poisoned MCP tool description](fieldcards/AI-019.md) | MCP | TEST | CTL-MCP-TRUST |
| [AI-020 — Tool change after approval](fieldcards/AI-020.md) | MCP | TEST | CTL-MCP-TRUST |
| [AI-021 — MCP token audience and scope](fieldcards/AI-021.md) | MCP | TEST | CTL-TOKEN |
| [AI-022 — MCP session and identity](fieldcards/AI-022.md) | MCP | TEST | CTL-SESSION |
| [AI-023 — MCP discovery and SSRF](fieldcards/AI-023.md) | MCP | TEST | CTL-EGRESS |
| [AI-024 — Local MCP server and permissions](fieldcards/AI-024.md) | MCP | TEST | CTL-ISOLATION |
| [AI-025 — API object authorization](fieldcards/AI-025.md) | PLATFORM | TEST | CTL-AUTHORIZATION |
| [AI-026 — API properties and role](fieldcards/AI-026.md) | PLATFORM | TEST | CTL-AUTHORIZATION |
| [AI-027 — API and inference limits](fieldcards/AI-027.md) | MODEL | TEST | CTL-BUDGET |
| [AI-028 — Sensitive logs and telemetry](fieldcards/AI-028.md) | PLATFORM | TEST | CTL-CONFIDENTIALITY |
| [AI-029 — RAG chain to simulated exfiltration](fieldcards/AI-029.md) | RAG | TEST | CTL-EGRESS |
| [AI-030 — Training poisoning](fieldcards/AI-030.md) | ML-DATA | TEST | CTL-POISONING |
| [AI-031 — Model artifact integrity](fieldcards/AI-031.md) | MODEL | TEST | CTL-INTEGRITY |
| [AI-032 — Insecure deserialization](fieldcards/AI-032.md) | MODEL | TEST | CTL-LOADER |
| [AI-033 — Dependencies and provenance](fieldcards/AI-033.md) | PLATFORM | TEST | CTL-SUPPLY |
| [AI-034 — Deployment secrets and identity](fieldcards/AI-034.md) | PLATFORM | TEST | CTL-AUTHORIZATION |
| [AI-035 — Execution isolation](fieldcards/AI-035.md) | PLATFORM | TEST | CTL-ISOLATION |
| [AI-036 — Deployment admission and rollback](fieldcards/AI-036.md) | PLATFORM | TEST | CTL-RELEASE |
| [AI-037 — Privacy through memorization](fieldcards/AI-037.md) | MODEL | TEST | CTL-PRIVACY |
| [AI-038 — Membership inference](fieldcards/AI-038.md) | MODEL | TEST | CTL-PRIVACY |
| [AI-039 — Guardrail or classifier evasion](fieldcards/AI-039.md) | LLM | TEST | CTL-POLICY |
| [AI-040 — OAuth consent in an MCP proxy](fieldcards/AI-040.md) | MCP | TEST | CTL-CONSENT |
| [AI-041 — Model behavior extraction](fieldcards/AI-041.md) | MODEL | TEST | CTL-SUPPLY |
| [AI-042 — SSRF in a URL retrieval tool](fieldcards/AI-042.md) | TOOLS | TEST | CTL-EGRESS |
| [AI-043 — Tool arguments and dispatcher](fieldcards/AI-043.md) | TOOLS | TEST | CTL-EXECUTION |
| [AI-044 — Binding and validity of human approval](fieldcards/AI-044.md) | TOOLS | TEST | CTL-INTENT |
| [AI-045 — RAG document ingestion and transformation](fieldcards/AI-045.md) | RAG | TEST | CTL-PROVENANCE |
| [AI-046 — Indirect injection from tool results](fieldcards/AI-046.md) | LLM | TEST | CTL-CONTEXT |
| [AI-047 — Classifier evasion through rephrasing and benign additions](fieldcards/AI-047.md) | MODEL | TEST | CTL-POLICY |
| [AI-048 — Protected attribute inversion](fieldcards/AI-048.md) | MODEL | TEST | CTL-PRIVACY |
| [AI-049 — Unavailable guardrail and alternate routes](fieldcards/AI-049.md) | LLM | TEST | CTL-POLICY |
| [AI-050 — Evaluator and rubric integrity](fieldcards/AI-050.md) | CORE | TEST | CTL-EVALUATION |
| [AI-051 — Distributed budget, queues and cancellation](fieldcards/AI-051.md) | AGENT | TEST | CTL-BUDGET |
| [AI-052 — Instructions in multimodal inputs](fieldcards/AI-052.md) | MULTIMODAL | TEST | CTL-CONTEXT-TRANSFORM |
| [AI-053 — Detection of and response to boundary violations](fieldcards/AI-053.md) | PLATFORM | TEST | CTL-OBSERVABILITY |
| [AI-054 — Shared responsibility with the AI provider](fieldcards/AI-054.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [AI-055 — Negotiated MCP capabilities and requests to the client](fieldcards/AI-055.md) | MCP | TEST | CTL-CONSENT |
| [AI-056 — Tool file path and workspace](fieldcards/AI-056.md) | TOOLS | TEST | CTL-ISOLATION |
| [AI-057 — Integrity of adapters, tokenizer and embeddings](fieldcards/AI-057.md) | PLATFORM | TEST | CTL-SUPPLY |
| [AI-058 — Memory isolation and lifecycle](fieldcards/AI-058.md) | AGENT | TEST | CTL-MEMORY |
| [AI-059 — External triggers and scheduled tasks](fieldcards/AI-059.md) | AGENT | TEST | CTL-INTENT |
| [AI-061 — Use of evaluation probes and detectors](fieldcards/AI-061.md) | CORE | TEST | CTL-EVALUATION |
| [AI-062 — Input and output safeguard integration](fieldcards/AI-062.md) | LLM | TEST | CTL-POLICY |
| [CORE-001 — Scope and rules of engagement](fieldcards/CORE-001.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-002 — Cross-checked architecture and inventory](fieldcards/CORE-002.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-003 — Threats and security requirements](fieldcards/CORE-003.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-004 — Accountability and identity](fieldcards/CORE-004.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-005 — Data, persistence and retention](fieldcards/CORE-005.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-006 — Provenance and changes](fieldcards/CORE-006.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-007 — Operation and recovery](fieldcards/CORE-007.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CORE-008 — Plan, evidence and decision](fieldcards/CORE-008.md) | CORE | DESIGN | CTL-GOVERNANCE |
| [CFG-001 — Effective permissions and credentials](fieldcards/CFG-001.md) | CORE | CONFIG | CTL-AUTHORIZATION |
| [CFG-002 — Data isolation and persistence](fieldcards/CFG-002.md) | CORE | CONFIG | CTL-ISOLATION |
| [CFG-003 — MCP host and transport configuration](fieldcards/CFG-003.md) | CORE | CONFIG | CTL-TOKEN |
| [CFG-004 — Loader, provenance and admission](fieldcards/CFG-004.md) | CORE | CONFIG | CTL-LOADER |
| [CFG-005 — Limits, streaming and guardrails](fieldcards/CFG-005.md) | CORE | CONFIG | CTL-BUDGET |
| [CFG-006 — Changes and delivery of AI components](fieldcards/CFG-006.md) | CORE | CONFIG | CTL-SUPPLY |
