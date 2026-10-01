# Inventory, capabilities and threats

## Building the system model

1. Record legitimate tasks, users, protected assets and business effects. Examples: reading one's own orders, summarizing authorized documents, creating drafts without sending them, classifying transactions without changing their training labels.
2. Inventory model/provider/version, parameters, prompts, guardrails, orchestration, APIs, identity, tools, MCP, consumers, data and dependencies. Include only the components that are present; note unknowns.
3. Trace origin → transformation → context/inference → decision → executor → resource → effect. Add cache, memory, queues, streaming, retries and deferred tasks where they exist.
4. For each flow, identify the authenticated principal, effective identity, permissions, data classification, authority, persistence, egress, owner and observability.
5. Check against deployment/configuration/traces. The model's self-description is a hint, not a reliable inventory source.

## Capabilities and routes

The available list is in `catalog/capabilities.json`. The template keeps UNKNOWN for information that is not yet confirmed. PRESENT and ABSENT require an evidence reference. Scope and access are recorded separately: `in_scope/out_of_scope` and `black-box/gray-box/white-box/none/unknown`.

A route groups a concrete boundary and identity. If two tools use different permissions, create two routes. If the same tool is tested directly and through an LLM with different assumptions, document separate routes or variants. Memory activates its tests without requiring an agent loop. An MCP stdio server does not inherit HTTP OAuth, RAG or language generation.

A case's condition is an OR between alternatives and an AND within each alternative. An omitted capability remains unknown. No case that depends on an unknown capability is marked not applicable. The plan keeps all decisions so that exclusions can be audited.

## Formulating threats

For each boundary write: "Actor A, with access B and control over C, can cause effect D on asset E by crossing boundary F". Attach the legitimate task, preconditions, expected control, impact, assumptions and decisive evidence.

Use STRIDE to ask about spoofing, tampering, repudiation, disclosure, exhaustion and elevation. Add AI-specific objectives: instruction changes through external data, persistent poisoning, purpose expansion, model/data tampering and information/behavior extraction.

RAG example: public source editor → indexed document → user A's context → tool with service identity → B's orders. Break it down into retrieval, injection, authorization and output hypotheses. Do not attribute the whole chain to the LLM if the backend admits B directly.

## Selecting and prioritizing

The catalog is activated by capabilities; the engineer prioritizes by exposure, privilege, resource value, persistence and impact. Basic cases are not replaced by reconnaissance. A technique's relation to a case guides execution; only task results with evidence increase coverage.

Before freezing, check that every critical route has sufficient threats and activities. If a case is missing, add it with an explicit control/oracle and a new catalog revision. Every exclusion keeps its reason, approver, expiry and residual risk. Do not delete rows to produce a report without pending items.

## Depth and shared responsibility

A black-box scope can demonstrate a textual leak or an external effect, but cannot prove the absence of improper chunks in the context. Record that limitation. For a SaaS provider, distinguish the integrator's obligations, the provider's documented commitments and non-observable aspects. Do not mark the provider's internal controls PASS based on a commercial claim.

The snapshot includes the app, available model, prompts, corpus/index, tools, permissions, guardrails and parameters. If the provider's version is not immutable, record the available identification and date, and limit comparisons.
