# LLM — Instructions, context and policies

## Preparation and inventory

Model/provider, instruction hierarchy, direct/indirect inputs, protected policy, reserved context and guardrails. Prepare a canary unknown to the input, a benign corpus and a rubric for the prohibited task.

## Walkthrough

1. Confirm the legitimate task and the direct refusal of a restricted request.
2. Test PI/JB mechanisms with one variable per trial; keep negatives, sessions and parameters.
3. Verify input/output transformations and decoded content without executing the result.
4. Also observe tools and effects if they exist; distinguish a leak, domain non-compliance and an improper action.
5. Evaluate guardrails separately and in chain, including timeout and streaming.

## Operational cases

| Case | Objective | Type |
|---|---|---|
| [AI-001](../fieldcards/AI-001.md) | Direct injection | TEST |
| [AI-003](../fieldcards/AI-003.md) | Exposure of protected context | TEST |
| [AI-010](../fieldcards/AI-010.md) | Unsupported citations and responses | TEST |
| [AI-039](../fieldcards/AI-039.md) | Guardrail or classifier evasion | TEST |
| [AI-046](../fieldcards/AI-046.md) | Indirect injection from tool results | TEST |
| [AI-049](../fieldcards/AI-049.md) | Unavailable guardrail and alternate routes | TEST |
| [AI-062](../fieldcards/AI-062.md) | Input and output safeguard integration | TEST |

## Interpretation and limits

An accepted DAN persona does not demonstrate a jailbreak. An out-of-domain response does not demonstrate evasion of every policy. Revealing a prompt without protected information does not by itself prove high impact.

## Evidence and closure

Each fieldcard defines evidence, oracle, variants, mitigations and retest. Keep the snapshot and the negative attempts. If an improper effect is confirmed, preserve minimal evidence and respect the stop condition; do not keep accumulating identical variants without purpose. Correct the failed boundary and repeat original, neighbor and benign.

The Merestone example inputs and their step-by-step application are in the [technique walkthroughs](../walkthroughs/). Record every adaptation; no example is considered executed because it is included in this guide.
