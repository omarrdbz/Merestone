# Technique library

Mechanisms are reused in boundary cases. Relating a technique is not the same as running a test. Merestone's own inputs are in the fieldcards and the step-by-step application in the [walkthroughs](walkthroughs/).

| Technique | Family / stage | Associated cases |
|---|---|---|
| REC-01 — Reconnaissance and surface map | REC / 1 | [AI-001](fieldcards/AI-001.md), [AI-006](fieldcards/AI-006.md), [AI-011](fieldcards/AI-011.md), [AI-015](fieldcards/AI-015.md), [AI-025](fieldcards/AI-025.md), [AI-033](fieldcards/AI-033.md) |
| PI-01 — Rule change and declared authority | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md), [AI-015](fieldcards/AI-015.md) |
| PI-02 — Narrative and context change | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-03 — Translating instructions into data | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-04 — Spell-checking and editorial transformation | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-05 — Summary, repetition and syntactic hints | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-06 — Encoded or obfuscated output | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-07 — Partial extraction and cumulative inference | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-003](fieldcards/AI-003.md) |
| PI-08 — Business-rule manipulation | PI / 2 | [AI-001](fieldcards/AI-001.md), [AI-014](fieldcards/AI-014.md), [AI-015](fieldcards/AI-015.md) |
| PI-09 — Indirect injection in structured records | PI / 2 | [AI-002](fieldcards/AI-002.md), [AI-008](fieldcards/AI-008.md) |
| PI-10 — Injection in web pages, documents and hidden content | PI / 2 | [AI-002](fieldcards/AI-002.md), [AI-029](fieldcards/AI-029.md) |
| PI-11 — Incoming email and automated decision | PI / 2 | [AI-002](fieldcards/AI-002.md), [AI-014](fieldcards/AI-014.md) |
| PI-12 — Tool result as instruction | PI / 2 | [AI-046](fieldcards/AI-046.md) |
| JB-01 — Unrestricted persona, DAN family | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-02 — Roleplay | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-03 — Fictional scenario and dialogue continuation | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-04 — Token smuggling | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-05 — Response prefix and affirmative continuation | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-06 — Adversarial suffix as a research variant | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-07 — Opposite/Sudo Mode | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| JB-08 — Infinitely Many Meanings: encoded input and output | JB / 3 | [AI-001](fieldcards/AI-001.md), [AI-039](fieldcards/AI-039.md) |
| OUT-01 — Interpreted HTML and reflected XSS | OUT / 4 | [AI-011](fieldcards/AI-011.md) |
| OUT-02 — Stored XSS through retrieval | OUT / 4 | [AI-011](fieldcards/AI-011.md), [AI-002](fieldcards/AI-002.md) |
| OUT-03 — SQL injection in generated values | OUT / 4 | [AI-012](fieldcards/AI-012.md) |
| OUT-04 — Text-to-SQL outside the authorized scope | OUT / 4 | [AI-012](fieldcards/AI-012.md), [AI-015](fieldcards/AI-015.md), [AI-025](fieldcards/AI-025.md) |
| OUT-05 — Write SQL in a read flow | OUT / 4 | [AI-012](fieldcards/AI-012.md), [AI-014](fieldcards/AI-014.md) |
| OUT-06 — Generated commands and code sent to an interpreter | OUT / 4 | [AI-013](fieldcards/AI-013.md) |
| OUT-07 — Function dispatcher that evaluates code | OUT / 4 | [AI-013](fieldcards/AI-013.md), [AI-015](fieldcards/AI-015.md) |
| OUT-08 — Legitimate function with a vulnerable implementation | OUT / 4 | [AI-012](fieldcards/AI-012.md), [AI-013](fieldcards/AI-013.md), [AI-025](fieldcards/AI-025.md) |
| OUT-09 — Exfiltration through Markdown/HTML images | OUT / 4 | [AI-029](fieldcards/AI-029.md), [AI-004](fieldcards/AI-004.md) |
| OUT-10 — Simple URL, preview and conditional exfiltration | OUT / 4 | [AI-029](fieldcards/AI-029.md) |
| OUT-11 — Hallucinations, citations and subsequent decision | OUT / 4 | [AI-010](fieldcards/AI-010.md) |
| OUT-12 — Hallucinated code and packages | OUT / 4 | [AI-010](fieldcards/AI-010.md), [AI-033](fieldcards/AI-033.md) |
| OUT-13 — Guardrail evasion through transformations | OUT / 4 | [AI-039](fieldcards/AI-039.md) |
| MCP-01 — Direct resources/tools/prompts surface | MCP / 5 | [AI-019](fieldcards/AI-019.md), [AI-025](fieldcards/AI-025.md) |
| MCP-02 — Errors and logs that leak data | MCP / 5 | [AI-028](fieldcards/AI-028.md) |
| MCP-03 — SQL injection through a resource URI | MCP / 5 | [AI-012](fieldcards/AI-012.md) |
| MCP-04 — Command injection in server tools | MCP / 5 | [AI-013](fieldcards/AI-013.md) |
| MCP-05 — SSRF in tool fetchers | MCP / 5 | [AI-042](fieldcards/AI-042.md) |
| MCP-06 — Tool poisoning in descriptions | MCP / 5 | [AI-019](fieldcards/AI-019.md), [AI-029](fieldcards/AI-029.md) |
| MCP-07 — Rug pull after approval | MCP / 5 | [AI-020](fieldcards/AI-020.md) |
| MCP-08 — Tool shadowing between servers | MCP / 5 | [AI-019](fieldcards/AI-019.md), [AI-029](fieldcards/AI-029.md) |
| MCP-09 — Transport, exposure and host isolation | MCP / 5 | [AI-021](fieldcards/AI-021.md), [AI-022](fieldcards/AI-022.md), [AI-024](fieldcards/AI-024.md), [AI-035](fieldcards/AI-035.md) |
| DATA-01 — Random label flipping | DATA / 7 | [AI-030](fieldcards/AI-030.md) |
| DATA-02 — Targeted label attack | DATA / 7 | [AI-030](fieldcards/AI-030.md) |
| DATA-03 — Clean-label poisoning | DATA / 7 | [AI-030](fieldcards/AI-030.md) |
| DATA-04 — Backdoor/Trojan by trigger | DATA / 7 | [AI-030](fieldcards/AI-030.md) |
| DATA-05 — Deserialization of untrusted artifacts | DATA / 7 | [AI-032](fieldcards/AI-032.md) |
| DATA-06 — Integrity and steganography in tensors | DATA / 7 | [AI-031](fieldcards/AI-031.md), [AI-032](fieldcards/AI-032.md) |
| DATA-07 — Feedback and continuous retraining | DATA / 7 | [AI-030](fieldcards/AI-030.md), [AI-008](fieldcards/AI-008.md) |
| APP-01 — IDOR and model-controlled identity | APP / 6 | [AI-025](fieldcards/AI-025.md), [AI-015](fieldcards/AI-015.md) |
| APP-02 — Administrator action induced by low-privilege data | APP / 6 | [AI-014](fieldcards/AI-014.md), [AI-029](fieldcards/AI-029.md) |
| APP-03 — Minimization, storage and logs | APP / 6 | [AI-028](fieldcards/AI-028.md), [AI-004](fieldcards/AI-004.md) |
| APP-04 — Approximate model extraction through queries | APP / 6 | [AI-041](fieldcards/AI-041.md) |
| APP-05 — Sponge inputs and inference consumption | APP / 6 | [AI-016](fieldcards/AI-016.md), [AI-027](fieldcards/AI-027.md) |
| APP-06 — Altered registry, serving and deployment | APP / 6 | [AI-031](fieldcards/AI-031.md), [AI-034](fieldcards/AI-034.md), [AI-036](fieldcards/AI-036.md) |
| APP-07 — Vulnerable frameworks and dependencies | APP / 6 | [AI-033](fieldcards/AI-033.md), [AI-036](fieldcards/AI-036.md) |
| MEM-01 — Contaminated persistent memory | AGENT / 5 | [AI-005](fieldcards/AI-005.md) |
| T-AI-006 — RAG retrieval ACL | RAG / 5 | [AI-006](fieldcards/AI-006.md) |
| RAG-01 — Knowledge revocation and deletion | RAG / 5 | [AI-007](fieldcards/AI-007.md) |
| RAG-02 — Ranking saturation | RAG / 5 | [AI-009](fieldcards/AI-009.md) |
| AGT-01 — Retry and idempotency | AGENT / 5 | [AI-017](fieldcards/AI-017.md) |
| AGT-02 — Delegation between agents | AGENT / 5 | [AI-018](fieldcards/AI-018.md) |
| T-AI-023 — MCP discovery and SSRF | MCP / 5 | [AI-023](fieldcards/AI-023.md) |
| API-01 — API properties and role | PLATFORM / 5 | [AI-026](fieldcards/AI-026.md) |
| T-AI-037 — Privacy through memorization | MODEL / 5 | [AI-037](fieldcards/AI-037.md) |
| PRV-01 — Membership inference | MODEL / 5 | [AI-038](fieldcards/AI-038.md) |
| MCP-10 — OAuth consent in an MCP proxy | MCP / 5 | [AI-040](fieldcards/AI-040.md) |
| T-AI-043 — Tool arguments and dispatcher | TOOLS / 5 | [AI-043](fieldcards/AI-043.md) |
| T-AI-044 — Binding and validity of human approval | TOOLS / 5 | [AI-044](fieldcards/AI-044.md) |
| T-AI-045 — RAG document ingestion and transformation | RAG / 5 | [AI-045](fieldcards/AI-045.md) |
| T-AI-047 — Classifier evasion through rephrasing and benign additions | MODEL / 5 | [AI-047](fieldcards/AI-047.md) |
| T-AI-048 — Protected attribute inversion | MODEL / 5 | [AI-048](fieldcards/AI-048.md) |
| T-AI-049 — Unavailable guardrail and alternate routes | LLM / 5 | [AI-049](fieldcards/AI-049.md) |
| T-AI-050 — Evaluator and rubric integrity | CORE / 5 | [AI-050](fieldcards/AI-050.md) |
| T-AI-051 — Distributed budget, queues and cancellation | AGENT / 5 | [AI-051](fieldcards/AI-051.md) |
| T-AI-052 — Instructions in multimodal inputs | MULTIMODAL / 5 | [AI-052](fieldcards/AI-052.md) |
| T-AI-053 — Detection of and response to boundary violations | PLATFORM / 5 | [AI-053](fieldcards/AI-053.md) |
| T-AI-055 — Negotiated MCP capabilities and requests to the client | MCP / 5 | [AI-055](fieldcards/AI-055.md) |
| T-AI-056 — Tool file path and workspace | TOOLS / 5 | [AI-056](fieldcards/AI-056.md) |
| T-AI-057 — Integrity of adapters, tokenizer and embeddings | PLATFORM / 5 | [AI-057](fieldcards/AI-057.md) |
| T-AI-058 — Memory isolation and lifecycle | AGENT / 5 | [AI-058](fieldcards/AI-058.md) |
| T-AI-059 — External triggers and scheduled tasks | AGENT / 5 | [AI-059](fieldcards/AI-059.md) |
| T-AI-061 — Use of evaluation probes and detectors | CORE / 5 | [AI-061](fieldcards/AI-061.md) |
| T-AI-062 — Input and output safeguard integration | LLM / 5 | [AI-062](fieldcards/AI-062.md) |
