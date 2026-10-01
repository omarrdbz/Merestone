# Instrumented local pilots

Six runs: three architectures, each with a vulnerable and a corrected control. The classifier uses a toy linear rule with fixed weights; it does not represent the performance of a trained model. RAG inspects retrieved context and uses a fixed text response; it does not evaluate an LLM's resistance. The agent uses scripted decisions and a minimal MCP stdio server in a subprocess, without OAuth, SDK or network.

Baseline, original, neighbor, benign, identity, reachability and effect are measured. The processes terminate and test data remain only in evidence. All other obligations remain NOT_RUN: all plans are still incomplete (code 2). A PASS on the corrected case does not certify the architecture.

- [classifier / vulnerable](classifier-vulnerable/report.md): AI-047 FAIL; 2/3 variants violate the oracle.
- [classifier / secure](classifier-secure/report.md): AI-047 PASS; 0/3 variants violate the oracle.
- [rag / vulnerable](rag-vulnerable/report.md): AI-006 FAIL; 2/3 variants violate the oracle.
- [rag / secure](rag-secure/report.md): AI-006 PASS; 0/3 variants violate the oracle.
- [agent-mcp / vulnerable](agent-mcp-vulnerable/report.md): AI-015 FAIL; 2/3 variants violate the oracle.
- [agent-mcp / secure](agent-mcp-secure/report.md): AI-015 PASS; 0/3 variants violate the oracle.

Review by another engineer: pending. Use the independent review form in templates/independent-review.md.
