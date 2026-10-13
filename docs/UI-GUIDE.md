# Using the local interface

Run `merestone ui` and keep its terminal open. The browser and CLI share the same workspace. If you start inside the framework folder, the welcome screen suggests a workspace under the sibling `assessments/` folder, outside the framework. You can replace that path before creating it.

## Prepare and save

1. In **Architecture**, describe the actor and each component of the route. Choose access, activities and scope, then select **Save route**. Empty components must be named or removed before saving.
2. Complete the readiness fields and save each changed field. Save load limits together with their **Save** button. The system name saves when you leave its field.
3. Set the source of the inventory answers, then answer the capability questions. Each answer saves immediately. Use **All capabilities** for capabilities outside the interview or when an interview question combines capabilities with different answers.
4. Define and save each test protocol: required variants, minimum trials, design, decision rule and justification.
5. Freeze the plan. The preview uses saved values; unsaved route, readiness, limit or selected-protocol edits must be saved first. Draft form entries remain only in the current browser page: save them before reloading or closing it.

**In scope** means the route is included in the assessment. **Out of scope** prevents completing its tasks; it does not turn them into passes or remove pending obligations. Review the owner's authorization before changing scope. **Access unknown** and **No access** describe visibility, separately from scope. After changing either on a frozen plan, save the route and freeze a revision with a reason and approver.

## Work through the plan

The **Selected** tab contains all tasks except those marked **Not applicable**, which have their own tab. Search, module and activity filters also apply to the counts on each tab. A task appears once for each route on which it is assessed.

Open a task to inspect its fieldcard, record a trial or review, and inspect evidence. Technical trials are staged first; **Decide** records the staged trials in the plan. A review uses documentary evidence directly. Wait for a save to finish before submitting another change. PASS still requires the frozen protocol, complete evidence and the engine's validation.

Evidence files are hashed locally and verified again on arrival. Wait for hashing to finish before submitting. A file may be at most 40 MB; the complete request, including base64-encoded files, must fit within 64 MB. Use smaller extracts or notes pointing to larger captures when needed.

## Revisions and reports

Changing Architecture does not change an existing frozen plan. Freeze a revision to apply saved changes; earlier results remain with the earlier plan and are not copied into the revision. Use **Report** for an HTML board, a printable document layout, Markdown, or both formats.

Exit code **2** means the assessment is incomplete or unverified. Code **1** means all selected obligations are resolved and at least one failed. Code **0** means selected obligations are resolved without failures and the required references verify. It is not a certification of the system.

## Keyboard and connection

- **Tab** moves between controls. **Enter** or **Space** opens a focused task or pending item.
- **1**, **2**, **3** open Architecture, Plan and Activity. **/** focuses task search.
- **E** opens report export; **T** changes the theme; **?** opens shortcut help.
- **Escape** closes a dialog or task panel. Dialog focus stays within the dialog and returns when it closes.
- Shortcuts are inactive while typing and while a dialog is open, apart from its own navigation and Escape.

If the server stops, restart `merestone ui` and use its newly printed link. Save errors appear in a message; check the message and the saved state before retrying. CLI edits are detected automatically while the page is visible. If the same route is also being edited in the browser, its local draft remains until it is saved or the page is reloaded.
