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

Draft form entries are held in the page and are lost on reload; the guide states this, and since the second pass the browser asks before leaving with unsaved architecture edits. Route saves used sequential CLI-backed field writes, so a mid-save failure could leave some fields saved; the [second pass](#route-editor-second-pass) replaces them with one atomic write. Concurrent changes from another browser or the CLI are not protected by optimistic locking. Full draft recovery, atomic saves across readiness fields and broader assistive-technology testing remain separate follow-up work.

## Route editor (second pass)

Branch: `fix/playbook-ux-audit`. Goal: a person new to Merestone can describe a route using only the interface, explain why a task is in the plan and which route it belongs to, and is never shown capabilities or trust boundaries they did not confirm. The product language (English) and visual style are unchanged; “route” stays as the secondary term under the title **Flow you will assess**.

### Findings and changes

| Finding | Change |
|---|---|
| “Route” was not explained; the card said only where information travels. | The card is titled **Flow you will assess** and defines a route as who starts the action, which components it passes through and what result it produces, with separate tasks, evidence and results per route. Three collapsible panels: an example, how the route shapes the plan, and when to add another route. |
| No worked example. | An illustrative document assistant (customer A user, may read only customer A documents, App → Document search → Model → Answer, check: customer B documents are never retrieved) loads into the draft only on request. It never changes access, activities, scope or capabilities, asks before replacing existing text, is labelled as illustrative and can be discarded. Every field hint uses the same example. |
| The actor's permissions and the assessor's access were easy to confuse. | Separate field **What they are allowed to do** (`actor_permissions`, optional) and **How much you can see: your access as assessor**. |
| Every connection between components was drawn as a numbered trust boundary. | Steps are drawn as plain circles. A boundary stone appears only on a step the user marked, with what changes: permissions, identity, authority or data trust, and an optional note (`trust_boundaries`, optional). Marks follow renamed components in the editor; removing a component clears the marks of the steps it joined; `set boundary` in the CLI drops marks that are no longer steps and says which. |
| The relation between route fields and the plan was implicit. | The plan panel lists what each part does: capabilities decide applicability, activities decide task types, actor/permissions/path/trust/check give context and add no task, access and scope decide whether results can be recorded, each route keeps its own tasks. Naming “search” or “model” in the path is stated not to confirm a capability; the card points out components that may relate to an unanswered capability. |
| The freeze preview showed three numbers per route from saved values only. | **Effect on the plan** under the editor: tasks by applicability and activity, examples with the reason for their state, and a side-by-side view of saved values and unsaved activities. Both come from `operational.expected_tasks`, the selection freezing uses (`GET /api/preview` for drafts). With a frozen plan it shows what a revision would add, remove or update on the route. |
| No way to add or remove routes. | **+ Add a route** (ID, activities copied, access unknown, capabilities unknown or copied with their sources, its own threat) and **Remove** for routes not in the frozen plan; for a route in the plan the dialog offers **Out of scope** instead. Tabs show each route's actor and result and mark unsaved drafts. Plans and evidence are never changed. Same rules in the new `merestone route` command. |
| A route save was several sequential CLI writes; a mid-save failure could leave some fields saved. | One `route edit` request validates every field (including trust marks against the final path) and writes the architecture once, or writes nothing. |
| Save state was only a button and a toast. | Status beside the button: **Unsaved** with the changed fields (and “edited” markers on fields), **Saving…**, **Not saved** with the reason while keeping the draft (also for refusals detected in the page), or **Saved** with whether the saved route matches the frozen plan. **Discard changes** with confirmation. The browser asks before leaving a page with unsaved architecture edits. |
| Opening a test task without a protocol created a pristine protocol form that the freeze guard reported as an unsaved change, with no way to discard it. | Forms that still hold only their defaults are not reported. |
| The revision explanation said only that results are not transferred. | The plan card states the next plan ID, tasks added/removed/updated per route (or that only descriptions change), where earlier results stay (record path) and that earlier plans and evidence are not rewritten. |
| A task did not say why it was in the plan. | **Why this task is in your plan**: the activity that generated it, the capabilities that made it applicable or pending (from the frozen route, not later edits), and the frozen actor, permissions, path, trust boundaries and check. The plan list has a route filter when there are several routes. |

### Compatibility

`actor_permissions` and `trust_boundaries` are optional properties added to the route in `architecture-v3` and in the architecture embedded in `plan-v3`. Selection does not read them, so obligations, task IDs and the obligations hash are unchanged; architectures and plans without them stay valid. A workspace created and frozen with the previous version (with a recorded review) was opened with the new CLI and interface: `check-plan` verifies it, the plan is not stale, and the route shows plain steps and “Saved · matches plan-001”. Adding a description afterwards makes the plan stale like any architecture edit; the revision text says that only descriptions change and where the earlier result stays. Older framework versions reject architectures that use the new fields, because the schemas forbid unknown properties.

### Verification

- Python: **91 tests passed** (83 earlier plus 8 for routes): atomic route edits and refusals that write nothing, trust marks validated against the path and pruned after path changes, route add/copy/remove rules, check stored in the route's own threat, unchanged obligations and pilot plans, preview and draft preview equal to the frozen plan per route, activity and applicability, revision summary equal to `governance.compare_plans`.
- Client: **29 tests passed** (13 earlier plus 16): example loading and confirmation, plain steps until marked, mark serialization by name, stale marks, component removal, freeze guard, discard, preview states, removal rules, frozen-route explanations, ID validation, pristine protocol forms, refusal status and frozen-plan status.
- Catalog and delivery validation pass; `git diff --check` is clean.
- Browser (Chromium through Playwright, 1440 × 1000, 1366 × 900, 1280 × 900 and 390 × 844, light and dark): empty route; example loaded into an empty route and, with confirmation, into a described one; save; draft activities preview; second route added from the help panel and described with the keyboard (step selected in the drawing with Enter, change toggled with Space); freeze blocked by unsaved edits with focus on **Save route**; freeze; route filter and task explanation; revision summary; removal refused for a frozen route and allowed for a new one; discard; rejected save and stopped server keep the draft and show the reason; leaving with unsaved edits asks first; legacy workspace. No horizontal overflow at 390 px and no JavaScript errors.

### Limits

The drawing is a fixed-width diagram that scrolls horizontally on narrow screens; the trust boundary list below it is the accessible and mobile equivalent. Reordering components requires removing and adding them. Trust marks are keyed by component names, so a step that appears twice in one path shares its mark. The route check is the hypothesis of the route's first threat; routes with several threats show only the first. Screen-reader behaviour was checked through names, roles and focus order, not with an assistive-technology session. A new person's ability to complete a route was assessed by walking through the interface, not by a usability study with participants.
