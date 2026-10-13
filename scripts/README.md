# Maintenance tools

The source of truth is the current catalog. For everyday use:

```console
python fieldguide.py validate-library
python fieldguide.py render
python scripts/verify_delivery.py
```

`verify_delivery.py` checks the catalog, generated views, walkthroughs, references and local links. It needs no external material: the framework is self-contained.

Run `python -m unittest discover -s tests -v` for the engine and local API. Run `node --test tests/test_ui_client.cjs` for client regressions; this uses Node's standard library and installs no packages. Node is a development-only requirement for this additional suite.

To add a capability, edit the vocabulary and the architecture contract; for a new field, update the schemas and semantic validation. Create a plan revision instead of modifying earlier snapshots. See [maintenance](../playbook/method/maintenance.md).
