# Playbook and UI audit — 2026-10-13

Branch: `fix/playbook-ux-audit`.

Reviewed the local interface, its save and planning workflows, the API tests, the entry guide, README, catalog consistency, generated fieldcards and local documentation links. The existing English product language is preserved. Test interactions used a disposable assessment, not an existing assessment or its evidence.

## Corrected findings

| Finding | Correction |
|---|---|
| Scope displayed `out of_scope`. | Explicit **In scope / Out of scope** labels, a named control group and an explanation of the consequences. Internal values are unchanged. |
| Out-of-scope tasks directed the user to access settings, sometimes on another route. | Scope and access have distinct messages and destinations; the affected route is selected. No access is distinguished from unknown access. |
| Freezing silently ignored unsaved route, readiness, limit and selected-protocol edits. | Show the unsaved sections, stop the freeze request and navigate to the first section needing a save. |
| Clearing an actor or removing all components could report a successful save while retaining old values. | Reject those invalid edits before writing and keep the draft for correction. A scope-only change on an unfinished initial route remains possible. |
| The frozen-plan message incorrectly claimed every edit saved immediately. | Explain the Save buttons, immediate capability saves and the need for a revision. Add a dedicated UI workflow guide. |
| Rapid submissions could issue duplicate writes. | Serialize client submission actions, report an in-progress save and release the guard after errors. This is a single-page safeguard, not cross-client transaction isolation. |
| Overlapping file reads could replace newer evidence with older bytes; an oversized dropped file could leave a stuck hashing slot. | Keep only the latest upload for a slot and validate size before occupying it. |
| Filter counts described the whole plan rather than visible matches; “All” excluded non-applicable tasks. | Counts follow the filters; rename the default tab to **Selected** and keep **Not applicable** separate. |
| Re-rendering lost focus on controls; some inputs and icon controls lacked useful accessible names. | Restore focus by binding or control identity, label readiness/evidence inputs, support keyboard activation of tasks and pending items, and connect task tabs to their panel. |
| Dialog focus could leave the dialog and page shortcuts remained active behind it. | Name dialogs, contain Tab navigation, suspend background shortcuts and restore focus on close. |
| Preview colors and shared logo palette variables were undefined. | Use defined theme colors and map the shared logo palette explicitly. Increase secondary-text contrast. |
| Capability columns had a fixed minimum width too large for narrow screens. | Allow columns to shrink to the available width; verify at 390 px. |
| View changes scrolled the window instead of the scrollable main panel. | Scroll and focus the main panel. Make the skip link visible on focus; hide route animation under reduced motion. |
| Starting the UI in the framework suggested a workspace path the CLI refused. | Suggest the sibling assessments directory while preserving the CLI restriction. |
| The welcome layout closed its wrapper prematurely. | Keep both welcome columns inside the intended wrapper. |

## Verification

- Python: **83 tests passed**, including API security checks, workspace creation, planning, evidence, revisions and reporting.
- Client: **13 tests passed**, using Node's standard test runner and the actual embedded application script. They cover scope, save/freeze guards, filtering, duplicate writes, upload races and palette references.
- Catalog validation: **75 cases, 31 controls, 85 techniques, 129 example inputs and 6 scenarios**.
- Delivery validation: generated fieldcards, 15 walkthrough families, 114 mappings and local documentation links pass. No catalog or generated security procedure was changed.
- Browser checks: edit actor/components/scope, block freezing with pending edits, save route, freeze plan, filter tasks, open a task with Enter, inspect the trial form, inspect export and contain its keyboard focus. Checked a 390 × 844 mobile viewport and a 1440 × 1000 desktop viewport, light and dark themes. The mobile capabilities view had no horizontal page or main-panel overflow. No JavaScript errors were observed in the inspected flows.

Commands from the framework directory:

```console
python -m unittest discover -s tests -v
node --test tests/test_ui_client.cjs
python fieldguide.py validate-library
python scripts/verify_delivery.py
git diff --check
```

The first Python run in a restricted Windows sandbox could not use loopback sockets and could not move staged evidence. The complete suite passed when rerun with local permissions; those environment failures were not product fixes. Node is needed only for the client regression tests; the application still uses Python's standard library without new runtime dependencies.

## Limits and follow-up

This is an implementation and UX review, not an independent security certification, external standards update, complete screen-reader conformance audit or validation against a production AI system. Historical verification records remain historical.

Draft form entries are held in the page and are lost on reload; the guide now states this explicitly. Route saves still use sequential CLI-backed field writes, so a mid-save failure may leave some fields saved; the UI reports the error and reloads saved state. Concurrent changes from another browser or the CLI are not protected by optimistic locking. Full draft recovery, atomic multi-field saves and broader assistive-technology testing remain separate follow-up work.
