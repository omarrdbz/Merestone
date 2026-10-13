# Using the local interface

Run `merestone ui` and keep its terminal open. The browser and CLI share the same workspace. If you start inside the framework folder, the welcome screen suggests a workspace under the sibling `assessments/` folder, outside the framework. You can replace that path before creating it.

## Describe the flow you will assess (route)

A **route** is one concrete flow through the system: who starts the action, which components it passes through and what result it produces. The plan keeps separate tasks (`CASE@ROUTE`), evidence and results for each route. The **01 · Route** card in **Architecture** is titled **Flow you will assess** and has three short help panels: an illustrative example, how the route shapes the plan, and when to add another route.

| Field | What to write | Example (the same illustrative flow throughout) |
|---|---|---|
| Who starts the action | A person, service or agent, with the identity it starts from. | Authenticated user of customer A |
| What they are allowed to do | The actor's legitimate permissions on this flow. Not your access as assessor. | Read only customer A documents |
| Path | Each component in order, ending with the result (an answer, a change or an action). | App → Document search → Model → Answer |
| Trust boundaries | Mark a step only where permissions, identity, authority or trust in the data change, and say what changes. | Actor → App: identity · App → Document search: permissions · Document search → Model: data trust · Model → Answer: nothing marked |
| What you will check | The control that must hold, written so a result can confirm or refute it. Stored as the route's threat. | Customer B documents are never retrieved |
| How much you can see | Your access as the assessor: black-box, gray-box or white-box. It does not change what the actor may do. | gray-box, with test accounts for customers A and B |
| Activities | Which kinds of tasks exist on this route. DESIGN adds the common design reviews; include it on at least one route. | DESIGN, CONFIG, TEST |
| Scope | In scope includes the route. Out of scope keeps its tasks visible but they cannot be completed. | In scope |

**Load this example** fills the editor with the flow above. It is illustrative, it never changes access, activities, scope or capability answers, and nothing is saved until you select **Save route**. If the route already has text, a confirmation asks before replacing it; **Discard changes** restores the saved route.

**Trust boundaries are explicit.** The drawing shows each step between components as a small circle; a boundary stone appears only on a step you marked. A connection between two components is not a trust boundary by default. Select a step in the drawing (or use the list under **Trust boundaries**) and choose what changes there: **Permissions**, **Identity**, **Authority** or **Data trust**, with an optional note. Marks follow the components when you rename them in the editor; removing a component clears the marks of the two steps it joined.

Naming a component such as “search” or “model” does not confirm any capability. The card points out components that may relate to an unanswered capability; answer it in **03 · Capabilities**.

### How a route shapes the plan

- **Capabilities** (03) decide which cases apply: applicable, pending confirmation while unknown, or not applicable when absent.
- **Activities** decide which kinds of tasks exist.
- **Actor, permissions, path, trust boundaries and check** give each task its context. They add or remove no task.
- **Access and scope** decide whether results can be recorded: unknown or no access, or out of scope, keeps tasks open.
- **Each route** keeps its own tasks, evidence and results.

The **Effect on the plan** panel under the editor is calculated by the planning engine (the same selection that freezing uses): the number of tasks on the route by applicability and activity, and a few example tasks with the reason for their state. It is labelled **Saved route** or, when activities have unsaved changes, shows the saved values next to **With your unsaved activities**. With a frozen plan it also says how many tasks a revision would add, remove or update on this route.

In the plan, a task's **Work** tab explains **why this task is in your plan** using the route as it was frozen: the activity that generated it, the capabilities that made it applicable or pending, and the route's actor, permissions, path, trust boundaries and check.

### When to add another route

Add a route when the actor, their permissions, the path or the effect changes; keep one route when only the wording of requests changes (those are test variants). For example, *read documents* (customer A user → App → Document search → Model → Answer) and *change an order* (customer A user → App → Model → Orders API → Order updated) are two routes. **+ Add a route** asks for a short ID (for example `ORDERS`) and whether to start capability answers as unknown (recommended) or copy them from the current route. Activities are copied; access starts unknown.

**Remove** is available only for routes that are not in the frozen plan. A route in the frozen plan cannot be removed: mark it **Out of scope** instead, so its tasks stay visible and anything recorded stays in that plan. Removing a route never changes a plan or an evidence file.

## Prepare and save

1. Describe each route as above and select **Save route**. All fields of the route are validated and written together, or nothing is written. The status next to the button shows **Unsaved** with the changed fields, **Saving…**, **Not saved** with the reason (your edits are kept), or **Saved**, and with a frozen plan whether the saved route matches it.
2. Complete the readiness fields and save each changed field. Save load limits together with their **Save** button. The system name saves when you leave its field.
3. Set the source of the inventory answers, then answer the capability questions. Each answer saves immediately. Use **All capabilities** for capabilities outside the interview or when an interview question combines capabilities with different answers.
4. Define and save each test protocol: required variants, minimum trials, design, decision rule and justification.
5. Freeze the plan. The preview uses saved values; unsaved route, readiness, limit or edited protocol forms must be saved or discarded first, and **Freeze** takes you to the first one. Draft form entries remain only in the current browser page: the browser asks before leaving a page with unsaved architecture edits.

**In scope** means the route is included in the assessment. **Out of scope** prevents completing its tasks; it does not turn them into passes or remove pending obligations. Review the owner's authorization before changing scope. **Access unknown** and **No access** describe visibility, separately from scope. After changing either on a frozen plan, save the route and freeze a revision with a reason and approver.

## Work through the plan

The **Selected** tab contains all tasks except those marked **Not applicable**, which have their own tab. Route (when there are several), search, module and activity filters also apply to the counts on each tab. A task appears once for each route on which it is assessed.

Open a task to inspect its fieldcard, record a trial or review, and inspect evidence. Technical trials are staged first; **Decide** records the staged trials in the plan. A review uses documentary evidence directly. Wait for a save to finish before submitting another change. PASS still requires the frozen protocol, complete evidence and the engine's validation.

Evidence files are hashed locally and verified again on arrival. Wait for hashing to finish before submitting. A file may be at most 40 MB; the complete request, including base64-encoded files, must fit within 64 MB. Use smaller extracts or notes pointing to larger captures when needed.

## Revisions and reports

Changing Architecture does not change an existing frozen plan. Freeze a revision to apply saved changes. The **05 · Plan** card says what the revision would do (tasks added, removed and updated per route, or only descriptions changed) and where earlier results stay: in the earlier plan's record, not copied into the revision; evidence files stay in the evidence store and earlier plans are never rewritten. Use **Report** for an HTML board, a printable document layout, Markdown, or both formats.

Exit code **2** means the assessment is incomplete or unverified. Code **1** means all selected obligations are resolved and at least one failed. Code **0** means selected obligations are resolved without failures and the required references verify. It is not a certification of the system.

## Keyboard and connection

- **Tab** moves between controls. **Enter** or **Space** opens a focused task or pending item.
- In the route drawing, **Tab** reaches each step; **Enter** or **Space** selects it and moves focus to its trust boundary buttons, which toggle with **Space**. Help panels open with **Enter**.
- **1**, **2**, **3** open Architecture, Plan and Activity. **/** focuses task search.
- **E** opens report export; **T** changes the theme; **?** opens shortcut help.
- **Escape** closes a dialog or task panel. Dialog focus stays within the dialog and returns when it closes. Confirmation dialogs start on the option that keeps your work.
- Shortcuts are inactive while typing and while a dialog is open, apart from its own navigation and Escape.

If the server stops, restart `merestone ui` and use its newly printed link. Save errors appear in a message and in the route's save status; check the message and the saved state before retrying. CLI edits are detected automatically while the page is visible. If the same route is also being edited in the browser, its local draft remains until it is saved, discarded or the page is reloaded.

The terminal equivalent of the route editor is `merestone route` (list), `merestone route edit ROUTE --actor ... --permissions ... --path ... --trust "FROM -> TO: CHANGES | NOTE" --check ...`, `merestone route add ID [--like ROUTE] [--copy-caps]` and `merestone route remove ID`.
