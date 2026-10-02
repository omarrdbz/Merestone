# Merestone 0.3 tools and contracts

## What each component does

| Entry point | Use | Limit |
|---|---|---|
| `merestone.py` (guided CLI) | Workspaces, guided inventory, status with next steps, readable task IDs, evidence recording with automatic hashes, demo | Convenience layer: writes the same records and calls the same checks; never relaxes a rule |
| `fieldguide.py` / `operational.py` | Capability-based selection, frozen plan, fieldcards, validation and reporting | Does not execute attacks or automatically interpret arbitrary evidence |
| `adapters/import_observations.py` | Imports trials and evidence from the instrumented system | The adapter/evaluator provides the observations and the judgment |
| `governance.py` | Plan revision, comparison and finding lifecycle | Checks consistency; does not authenticate the approver's identity or authority |
| `adapters/local_pilots.py` | Three fixtures with vulnerable/corrected controls | Toy classifier, fixed RAG response and minimal MCP stdio; not a production model |
| `jsonutil.py` | Strict JSON reading/writing, canonical hashing and the schema subset used by the contracts | Not a universal JSON Schema validator |

## Editable source and contracts

Canonical catalog: `catalog/{controls,cases,techniques,examples,scenarios}/index.json`. Capability/applicability is an OR of AND clauses with present/absent/unknown states. Selection instantiates case+asset+route+actor+activity; a technique can be reused at different boundaries. Conceptual relations do not create results.

3.0 contracts in `schemas/`: architecture, plan, experimental protocol, trial, evidence, finding and per-entity catalogs. Fields, IDs, relations, uniqueness, hashes and state rules are validated. The local validator uses a documented subset of JSON Schema: type, properties, required, additionalProperties=false, enum, items, sizes, uniqueItems, pattern, bounds and anyOf. It is not a universal validator. The schemas can also be checked with Draft 2020-12.

The catalog, the architecture and the full list of obligations are bound to the plan by hash. Store its manifest separately in controlled storage. Each evidence item requires a relative path inside the store, bytes and SHA-256. Upward paths and files outside the store are not accepted. Hashes detect changes against a trusted reference; they do not authenticate the collector.

Every decided TEST/REDTEAM needs a frozen protocol: variants, minimum valid trials per variant, experiment design, rule and justification. The checker requires the planned sample for a PASS. A FAIL is not hidden by pending variants, which remain visible. DESIGN/CONFIG use documentary review; they do not need simulated attacks.

## Importing an observation

The event JSON has exactly: task_id, result, observations, reviewer, cleanup_confirmed, trials and evidence. Each trial follows `trial-v3.schema.json`; each evidence item follows `evidence-v3.schema.json`. You can use the events of [the pilots](../examples/pilots-final/README.md) as an example, replacing all lab data with measurements from the authorized system.

```console
python adapters/import_observations.py --plan runs/plan.json --event private/event.json --manifest runs/plan.json.manifest.json --evidence-root private/evidence --out runs/observed-plan.json
```

The original manifest remains valid because the obligations did not change. The importer adds trials without overwriting earlier evidence and preserves FAIL. It does not turn a scanner report into a PASS without baseline, reachability, identity and effect.

## Revising and comparing plans

```console
python governance.py revise --plan runs/observed-plan.json --architecture runs/new-architecture.json --reason "Permission change and retest" --approver "Plan owner" --out runs/retest-plan.json
python governance.py compare runs/observed-plan.json runs/plan-retest.json
```

A revision creates a new ID and manifest, keeps the link to the previous one and starts without results. The comparison lists added, retired and modified obligations; it does not transfer PASS. To verify historical plans with another catalog, also keep the previous framework version and the snapshot. The current CLI rejects incompatible snapshots instead of silently recalculating them.

## Validating a finding

```console
python governance.py check-finding --finding private/finding.json --plan runs/observed-plan.json --manifest runs/plan.json.manifest.json --evidence-root private/evidence
```

To close, add `--retest-bundle private/retests.json`: a list of objects with plan, manifest and evidence_root paths, relative to that file. History, dates, task/evidence references, temporary acceptance and revalidation of the original boundary are validated. Technical closure needs distinct original/neighbor/benign trials; documentary closure needs a review of the correction. The reviewer of a high/critical finding must differ from the owner. Real independence and authorization remain a human check.

To include verified findings in the report, add the option `--findings private/finding.json` to `fieldguide.py report` (it accepts several files). For closed findings also add `--retest-bundle`. Cause, evidence, impact, owner, correction and closure criterion are shown alongside coverage and pending items.

## Lab generation and execution

```console
python fieldguide.py render
python -m unittest discover -s tests -v
python adapters/local_pilots.py --out runs/new-pilots
```

Fieldcards are regenerated from the catalog. Plans, reports and pilots require a new output to preserve history. `scripts/verify_delivery.py` checks catalog consistency, generated views, walkthroughs, references and links.

## Guided CLI (merestone.py)

`merestone.py` is a convenience layer over the engine. Install the command with `python -m pip install -e .` from the framework folder (editable install; the CLI reads the catalog from this folder). It keeps every contract: plans, manifests, evidence and trials are the same JSON records, decisions go through the observation importer, and `check-plan` remains the source of truth. What it removes is bookkeeping.

| Command | What it does |
|---|---|
| `new <folder> --profile P [--guided]` | Creates a workspace (`merestone.json`, `architecture.json`, `evidence/`, `plans/`, `manifests/`, `reports/`, `staging/`). `--guided` asks 16 yes/no/unsure questions that set capabilities; unsure answers stay `unknown`. |
| `setup` | Asks, one by one and in plain language, for everything needed before freezing the plan: permission, version under test, inventory reviewer and source, stop conditions, load limits, access, actor and boundary. Enter skips an item. |
| `status` / `check [--json]` | Exit code, coverage by module and the next concrete commands. Before a plan exists it shows a checklist: what each item means, why it matters and the command that sets it. `plan` refuses to freeze while blocking items (readiness gaps and unknown access) remain, unless `--anyway` is passed. |
| `caps`, `set`, `protocol` | Edit capabilities (with `--source`), scope and readiness fields, and frozen test protocols without editing JSON. |
| `plan [--reason --approver] [--anyway]` | Freezes `plans/plan-NNN.json`, its manifest and a Markdown guide. A later change requires a reason and approver and produces a revision (via `governance.revise_plan`); results are never transferred. |
| `tasks`, `show <TASK>` | Readable IDs `CASE@ROUTE` (or the case ID when unique), the fieldcard and the exact recording commands. |
| `record <TASK> ...` | Stages one trial. Evidence files (`--evidence KIND=FILE`) or short notes (`--note KIND="..."`) are copied into `evidence/` and hashed (SHA-256, size, timestamp, collector). |
| `decide <TASK> ...` | Builds the import event from the staged trials and commits it as a new plan record (`plan-NNN.rMMM.json`). PASS requires the full planned sample; any FAIL trial makes the task FAIL. |
| `review <TASK> ...` | Records a DESIGN/CONFIG decision with documentary evidence of kind `review`. |
| `report [--format md\|html\|both] [--layout board\|document] [--open]` | Writes the report into `reports/`. `html` is a self-contained, read-only view in one of two layouts: `board` (default, a dashboard with task columns and a details panel) or `document` (top to bottom: verdict, a field of boundary stones per module, what needs attention, then every obligation; prints with all details expanded). Both are self-contained (no network, strict Content-Security-Policy, all text escaped) and show the exit code, readiness, coverage by module, every task by state and, per task, protocol, trials, hashed evidence and the fieldcard. It presents what `check-plan` computed and never re-decides anything. |
| `ui [--port N] [--no-browser]` | Local web interface (`ui_server.py` + `ui/app.html`, standard library only): architecture editor with the route as boundary stones, readiness fields, capabilities (switches or a 16-question interview, each answer stored with its source), protocols, freeze and revision; plan board by state with fieldcards; trial and review forms with drag-and-drop evidence; status light, pending list and report export. Every write calls the same command functions (`cmd_set`, `cmd_caps`, `cmd_protocol`, `cmd_plan`, `cmd_record`, `cmd_decide`, `cmd_review`, `cmd_report`), so no rule is relaxed. Safeguards: binds to 127.0.0.1 only; the Host header must name that address (DNS rebinding); a random session key given once in the printed link and then kept in an `HttpOnly`, `SameSite=Strict` cookie; API calls need a custom header and, for writes, a same-origin `Origin`; strict Content-Security-Policy with a per-response script nonce; evidence is hashed in the browser and re-hashed on arrival (a mismatch is refused before anything is stored); reports are served only by exact file name. The page polls a change marker, so edits made in the terminal appear without reloading. |
| `demo`, `doctor`, `fieldcard`, `list` | The local pilots with a narrated summary, environment checks, and catalog browsing. |

Records are append-only: the frozen plan is never rewritten, each decision produces a new record and the workspace `history` logs every action. Keep a copy of `manifests/` outside the workspace (or create it with `--manifest-dir`) so the approved manifest stays under separate control.

## Implementation limits

The delivery is an operational playbook with local tools. It does not include a multi-user service, signatures, enterprise encryption/retention, universal connectors, ticket management or automatic execution of all procedures. Controls are verified through fieldcards and specific adapters. The pilots test the local walkthrough, not the security of a real system.
