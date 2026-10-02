# Merestone 0.3.0 verification

The check distinguishes implementation, catalog consistency and evaluation of a target. Python 3.10+ standard library; no network.

## Implementation results

- **80 tests passed**: planning, evidence, protocols, import, tracking, reporting, the JSON/schema utilities, the guided CLI (`merestone.py`), the HTML report and the local web interface (`merestone ui`: session key, Host and Origin checks, hash re-verification and the same rules as the CLI). [Full output](test-results.txt).
- **75 cases, 31 controls, 85 techniques, 129 example inputs and 6 scenarios** with verified references and relations.
- Selection distinguishes RAG without tools and MCP stdio without LLM/OAuth. It accepts the same case on two assets and rejects deleted tasks/modified frozen fields.
- PASS requires verifiable evidence, baseline, reachability, identity, effect, cleanup and a predefined sample/variants. Byte corruption, paths outside the store, hidden FAIL, changed snapshots and an earlier block confused with later resistance are detected.
- Tracking checks history, references, expiry and closure with revalidation; documentary closure does not require inventing attacks. Revised plans keep a link to the previous one and do not inherit results.
- The contracts are checked by the local validator (`jsonutil.py`) and by the suite. An independent Draft 2020-12 validator is optional and not bundled.

## Catalog, examples and walkthroughs

[Final verification record](verification-final.json): 75 cases, 31 controls, 85 techniques, 129 example inputs, 15 technique walkthroughs and 114 mappings with metadata. All local links reviewed exist; every generated view matches the catalog.

Example inputs and walkthroughs are Merestone-original and regenerated from the catalog by `render`; the framework is self-contained.

## Operational flow pilots

[Results and evidence of the three labs](../examples/pilots-final/README.md).

| Fixture | Case | Vulnerable configuration | Corrected configuration | Scope |
|---|---|---|---|---|
| Toy linear classifier | AI-047 | Original and neighbor violate; benign works | Three variants PASS | Fixed parameters; not a representative trained model |
| Retrieval without tools | AI-006 | B chunks reach A's context | ACL excludes B; benign works | Instrumented retrieval; generative response replaced by fixed text |
| Scripted agent + minimal MCP stdio | AI-015 | Server accepts other users' orders | Server limits reads to principal A | JSON-RPC messages and local subprocess; not a full evaluation of SDK, OAuth or LLM |

Six runs, 18 trials and 108 evidence artifacts. Each vulnerable configuration produces a finding with cause/evidence and the corrected version provides revalidation. The findings are ready for independent review, not closed by a fictitious approval. All plans return **2, incomplete**, because only the pilot's case was run and all other obligations remain NOT_RUN.

## Verification limits

No production system was evaluated. The example inputs are Merestone-original fixtures, not a real target. Hashes and states verify consistency, not the collector's authenticity or the correctness of each technical judgment.

Review by another engineer and validation on real architectures remain pending that person and environment. The [protocol for carrying them out](../templates/independent-review.md) is ready.

## Repeating the checks

```console
python fieldguide.py validate-library
python -m unittest discover -s tests -v
python scripts/verify_delivery.py
```
