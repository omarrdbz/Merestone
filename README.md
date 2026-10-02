# Merestone 0.3.0 — Operational AI security playbook

*Know where every boundary lies.*

A *merestone* was the stone that marked where one piece of land ended and the next began. Merestone applies that idea to AI systems: the risk lives in the routes and the trust boundaries they cross, not in the model alone.

Modular assessment by architecture, asset, identity and boundary. It includes the method, technical fieldcards, examples, scenarios, planning and evidence validation. The entry point is the **[operational playbook](playbook/start.md)**.

The library contains 75 cases (8 common design reviews, 6 configuration reviews and 61 from the AI catalog), 31 controls, 85 techniques, 129 example inputs and 6 scenarios. Every example and walkthrough is Merestone-original and self-contained; nothing external is required to run an assessment.

1. [Prepare architecture, scope and threats](playbook/architecture/inventory-and-threats.md).
2. [Select modules and follow the method](playbook/start.md).
3. [Consult fieldcards with procedure, evidence and oracle](playbook/catalog.md).
4. [Apply techniques step by step in the walkthroughs](playbook/walkthroughs/).
5. [Record findings, correct and retest](playbook/method/findings-and-regression.md).

### Quick start (guided CLI)

```console
merestone demo                                             # watch a FAIL become a PASS in a minute
merestone new ../assessments/my-eval --profile rag --guided   # workspace + 16 plain-language questions
cd ../assessments/my-eval
merestone setup                                            # permission, version, limits, access... one question at a time
merestone status                                           # what is missing and the exact command to fix it
merestone plan                                             # freeze the plan
merestone tasks --state todo                               # readable task IDs such as AI-006@ROUTE-1
merestone show AI-006@ROUTE-1                              # fieldcard, protocol and how to record it
merestone record AI-006@ROUTE-1 --variant original ...     # evidence is copied and hashed for you
merestone decide AI-006@ROUTE-1 --reviewer "..." --observations "..." --cleanup-confirmed
merestone report --format html --open                      # visual dashboard to share; works offline (--layout document for a printable report)
```

### Visual interface (local web app)

```console
merestone ui                                               # opens the browser on 127.0.0.1; Ctrl+C stops it
```

The same workflow without the terminal: an architecture editor (the route drawn as boundary stones, readiness fields, capabilities as switches or a 16-question interview, test protocols, freezing and revisions), a plan board with each task's fieldcard, trial and review forms where evidence files are dropped in and hashed (SHA-256) automatically, an always-visible status light and pending list, and report export (board or document). It runs only on this computer with the standard library, sends nothing to the network, and every change goes through the same commands and checks as the CLI, so both can be used on the same workspace at the same time. Light and dark themes. Without a workspace it offers to create or open one. Options: `--port`, `--no-browser`.

**Install the `merestone` command once** (from this folder, Python 3.10+; no dependencies are downloaded):

```console
python -m pip install -e .
```

After that, `merestone` works from any folder. If Python is installed for all users (for example `C:\Python312` on Windows) and pip reports a permission or `.deleteme` error, install it for your user instead: `python -m pip install --user -e .`. If pip then warns that its `Scripts` folder is not on `PATH`, either add that folder to `PATH` or use `python -m merestone ...`, which works from any folder. Keep assessment workspaces **outside** this folder: they hold evidence and must never be committed (`merestone new` refuses to create them here). Without installing, run `python <framework>/merestone.py ...`, or add this folder to `PATH` to use the `merestone` / `merestone.cmd` launchers. The guided CLI writes the same records and applies the same checks as the commands below. See [tools and contracts](docs/IMPLEMENTATION.md#guided-cli-merestonepy).

### Engine commands

```console
python fieldguide.py validate-library
python fieldguide.py init --profile rag --out runs/architecture.json
```

Complete the inventory, verified capabilities, threats and protocols before generating the plan:

```console
python fieldguide.py plan --architecture runs/architecture.json --out runs/plan.json
python fieldguide.py check-plan runs/plan.json --manifest runs/plan.json.manifest.json --evidence-root private/evidence
```

A new plan returns code 2 because its tests are pending. Deleting tasks, hiding failures or reducing the frozen variants does not allow it to be approved. The profiles are drafts, not statements about existing components.

The CLI uses only the Python standard library (3.10+). It does not execute the example inputs or send attacks to external systems. It includes an observation importer and lab pilots. Its checks do not authenticate the assessor or replace independent technical review.

- [Tools and contracts](docs/IMPLEMENTATION.md).
- [Verification and pilots](docs/VERIFICATION.md).
- [References and mappings](playbook/method/references.md).
- [Maintenance and contributions](playbook/method/maintenance.md).

Terminology: [glossary](playbook/method/glossary.md). Mapping between the entry guide and phases 0–9: [section 0 of the playbook](playbook/start.md).

## Acknowledgment

The structure of this framework was inspired in part by the AI Red Teamer path of HTB Academy. All content here — method, fieldcards, techniques, examples and walkthroughs — is Merestone's own; no third-party course text, prompt or material is included or redistributed.

## License

Copyright 2026 omarrdbz. Licensed under the [Apache License, Version 2.0](LICENSE); see [NOTICE](NOTICE).
