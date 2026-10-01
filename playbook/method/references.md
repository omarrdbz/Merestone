# Sources and mapping decisions

Initial consultation: September 27, 2026. OWASP/MCP/NIST consulted again on September 28, 2026. All external IDs re-verified against the published sources on October 1, 2026 (see [verification record](#verification-of-external-mappings-2026-10-01)). The Merestone procedures are original. The mappings are analytical associations for traceability, not regulatory equivalences, complete coverage or endorsement by the cited organizations.

| ID | Source/versioning | Use |
|---|---|---|
| OWASP26 | [Official repository, final 2026 list](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/README.md) | Risk category per case; the page states publication on August 4, 2026 |
| OWASP25 | [OWASP LLM 2025 archive](https://genai.owasp.org/llm-top-10/) | Earlier edition, kept for comparison with the 2026 list |
| NIST | [AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | Organization of the risk management process |
| NIST-GAI | [NIST AI 600-1, 2024](https://doi.org/10.6028/NIST.AI.600-1) | Complementary generative AI profile; specific controls are not attributed without a detailed mapping |
| API | [OWASP API Security 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/) | Object/property authorization, consumption and SSRF |
| MCP | [MCP specification 2025-11-25: Security Best Practices](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices), [Sampling](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) and [Elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) | Confused deputy, token passthrough, SSRF, session hijacking, local server compromise and client-side requests; the pages may evolve |
| ATLAS | [Official MITRE ATLAS 2026.09 data](https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/v6/ATLAS-2026.09.yaml) | Cases with verified techniques; content version 2026.09 and format 6.0.0 |
| AGENTIC | [OWASP Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | Partial relations ASI02, ASI06, ASI07 and ASI09; they do not represent comprehensive coverage |

## Version handling

OWASP LLM **2026** is chosen for new mappings. The archive page still shows 2025, so every reference includes the year. Indicative category correspondences, subject to reviewing their scope: 2025 LLM01→2026 LLM01; LLM02→LLM02; LLM03→LLM04; LLM04→LLM05; LLM05→LLM10; LLM06→LLM03; LLM07→LLM08 (expanded scope); LLM08→LLM09; LLM09→LLM07; LLM10→LLM06. Do not treat this table as equality of definitions. Consult the earlier OWASP sources.

## Mapping of the NIST AI RMF 1.0 process

| Function | Use in Merestone | Process evidence |
|---|---|---|
| GOVERN | Owners, authorizations, criteria and acceptance | Charter, policies and decisions |
| MAP | Context, architecture, assets and threats | Inventory and threat model |
| MEASURE | Tests, metrics and uncertainty | Runs, evidence and evaluation |
| MANAGE | Remediation, retest and monitoring | Tickets, closures and regression |

Mapping proposed by Merestone at the function level; it does not attest compliance with NIST subcategories. The cases keep MEASURE as a process alignment, distinguished from `related-risk` for OWASP.


## Local sources

The example inputs and the step-by-step [walkthroughs](../walkthroughs/) are Merestone-original and self-contained. They were authored for this framework.

Additional references: [NIST AML E2025](https://csrc.nist.gov/pubs/ai/100/2/e2025/final) for ML terminology and [ASVS](https://owasp.org/projects/asvs) for application controls. They are cited without attributing compliance or inventing specific controls.

## Reproducible record

The [114 mappings](../../catalog/mappings/index.json) separate entity, version, ID, relation, justification, scope, URL, date and editorial reviewer. The [reference snapshot](../../catalog/sources/reference-snapshot.json) and [its hash](../../catalog/sources/references.json) keep the normalized facts used for mapping. They are not a complete copy of the official pages or an upstream commit; that commit was not available. Keep the catalog together with each assessment.

## Verification of external mappings (2026-10-01)

Every external ID used in the catalog was checked against the published source. Result: all IDs exist and the relations are consistent with the cited definitions. No mapping had to be removed.

| Framework | Checked against | Result |
|---|---|---|
| OWASP LLM 2026 | Official 2026 README (published August 4, 2026): LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Excessive Agency, LLM04 Supply Chain, LLM05 Data and Model Poisoning, LLM06 Unbounded Consumption, LLM07 Misinformation, LLM08 Hidden Context Exposure, LLM09 Vector and Embedding Weaknesses, LLM10 Improper Output Handling | 42 mappings consistent; the 2025→2026 correspondence table above is correct |
| MITRE ATLAS 2026.09 | ATLAS data 2026.09: AML.T0051 (.000 direct, .001 indirect), AML.T0020 Training Data Poisoning, AML.T0010 AI Supply Chain Compromise (.001 AI Software, .003 Model), AML.T0024.000 Infer Training Data Membership | 10 mappings consistent |
| OWASP Agentic 2026 | Published list (December 9, 2025): ASI02 Tool Misuse and Exploitation, ASI06 Memory and Context Poisoning, ASI07 Insecure Inter-Agent Communication, ASI09 Human-Agent Trust Exploitation | Consistent; the time-stamped download link was replaced by the stable resource page; AI-005 → ASI06 added |
| OWASP API 2023 | API1 BOLA, API3 BOPLA, API4 Unrestricted Resource Consumption, API7 SSRF | Consistent |
| NIST AI RMF 1.0 / AI 100-2 E2025 | Playbook (GOVERN, MAP, MEASURE, MANAGE); AI 100-2 E2025 (March 24, 2025) covers evasion and privacy attacks | Consistent; function-level alignment only |
| MCP 2025-11-25 | Security Best Practices, Sampling and Elicitation pages | The generic AI-055 → security_best_practices relation was imprecise (that page does not cover sampling or elicitation) and now points to the Sampling and Elicitation security considerations. Specific sections added for AI-021 (token passthrough), AI-022 (session hijacking), AI-023 (SSRF), AI-024 (local server compromise) and AI-040 (confused deputy) |

Limits: the ATLAS sub-technique names were confirmed through the ATLAS data and secondary listings because the full YAML is too large to review in one pass; recheck it when ATLAS publishes a new version. Mappings remain analytical relations, not equivalence or certification.
