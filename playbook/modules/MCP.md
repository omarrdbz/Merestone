# MCP — Host, client, server and transport

## Preparation and inventory

Roles per asset, version, handshake/capabilities, resources/tools/prompts, stdio/HTTP, identity and trust per server. Distinguish a vulnerable server from a malicious server.

## Walkthrough

1. Review the effective configuration and capabilities; enumerate surfaces per role with a direct client.
2. Test the server implementation reusing authorization, SQL, code, path and egress controls.
3. On the host/client, evaluate descriptions, results, tool changes and collisions between servers.
4. Over HTTP/OAuth, test audience/scope/issuer/validity, session and per-client consent; discovery as a separate fetcher.
5. Over stdio, evaluate the binary/command, permissions, environment and process limits.
6. Evaluate sampling/elicitation only if they are negotiated; record consent and the data delivered.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-019](../fieldcards/AI-019.md) | Poisoned MCP tool description | TEST |
| [AI-020](../fieldcards/AI-020.md) | Tool change after approval | TEST |
| [AI-021](../fieldcards/AI-021.md) | MCP token audience and scope | TEST |
| [AI-022](../fieldcards/AI-022.md) | MCP session and identity | TEST |
| [AI-023](../fieldcards/AI-023.md) | MCP discovery and SSRF | TEST |
| [AI-024](../fieldcards/AI-024.md) | Local MCP server and permissions | TEST |
| [AI-040](../fieldcards/AI-040.md) | OAuth consent in an MCP proxy | TEST |
| [AI-055](../fieldcards/AI-055.md) | Negotiated MCP capabilities and requests to the client | TEST |
| [AI-042](../fieldcards/AI-042.md) | SSRF in a URL retrieval tool | TEST |
| [AI-043](../fieldcards/AI-043.md) | Tool arguments and dispatcher | TEST |
| [CFG-003](../fieldcards/CFG-003.md) | MCP host and transport configuration | CONFIG |

## Interpretation and limits

MCP does not imply RAG or an LLM. SQLi through a URI and token passthrough are different failures. The host's UI control does not replace server authorization. A capability that is not enabled remains not applicable, not PASS.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
