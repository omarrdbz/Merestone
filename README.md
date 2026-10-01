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
