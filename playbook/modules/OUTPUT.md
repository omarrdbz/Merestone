# OUTPUT — Output consumers

## Preparation and inventory

All real consumers: HTML/Markdown, SQL, code, function, URL, file, message and decision. Prepare an isolated renderer, ephemeral DB and fixture interpreter/sink as appropriate.

## Walkthrough

1. Inject synthetic output into the consumer to check the deterministic control.
2. Verify the specific context: HTML vs JS/CSS encoding; structural SQL vs a valid but improper query; argv vs shell.
3. Try to produce the same stimulus through the LLM and record the route difference.
4. Separate URL generation, automatic preview and user click; measure actual receipt of the canary.
5. Verify grounding/citations and generated dependencies before a decision or installation.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-011](../fieldcards/AI-011.md) | Output to HTML | TEST |
| [AI-012](../fieldcards/AI-012.md) | Output to SQL | TEST |
| [AI-013](../fieldcards/AI-013.md) | Output to a code executor | TEST |

## Interpretation and limits

Printing SELECT is not execution. Allowed HTML is not XSS. A generated URL is not received exfiltration. An invented package is a quality signal; installing it without control demonstrates another boundary.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
