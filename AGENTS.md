# FirstWindow Project Instructions

## Product contract

FirstWindow is a beginner-first, free-first launcher for coding agents.

The default `$0 Mode` MUST NOT silently invoke a provider whose cost status is unknown.

## Mandatory preflight

Before substantial work:

1. Read `PROJECT_STATE.json`.
2. Read `docs/EXECUTION_CONTROL.md`.
3. If status is `post-release`, also read `docs/LAUNCH_CONTROL.md`.
4. Confirm the requested work matches the active objective/issue.
5. Freeze scope, non-goals, acceptance criteria, risk boundaries, and stop conditions.
6. Use one primary engineering issue per implementation branch.

If project state, chat context, and issue scope disagree, repository state wins until explicitly updated.

## Required checks

```bash
python scripts/validate.py
python scripts/check_project_state.py
python -m compileall -q src scripts tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows distribution also requires the **Windows App** GitHub Actions workflow to build and pass the packaged `--self-test`.

## Engineering rules

- Python 3.10+ and zero runtime dependencies for the core CLI/GUI.
- Keep routing policy separate from runtime adapters.
- Never store API keys, OAuth tokens, or provider secrets in task state.
- Query only non-secret Hermes model configuration for local-runtime detection.
- Reject path traversal and unsafe task IDs.
- Worker output is not acceptance evidence.
- Persist runtime task/checkpoint/evidence under `.firstwindow/tasks/<task_id>/`.
- Persist repository-level phase/queue/resume state in `PROJECT_STATE.json`.
- `$0 Mode` stops instead of falling back to unknown-cost providers.
- Network installer commands are allowlisted to official Agnes/Hermes installer endpoints and require explicit confirmation.
- Do not mutate Agnes or Hermes credentials automatically.
- Do not perform shutdown, restart, sleep, or power operations.
- Prefer existing Agnes/Hermes capability over adding another runtime or dependency.
- Update `PROJECT_STATE.json.resume_point` before long-task handoff or context switch.

## Post-release operating rules

When `PROJECT_STATE.status == "post-release"`:

- the released product baseline stays frozen;
- `active_engineering_issue` is null and `engineering_queue` is empty;
- the first item in `launch_track` is the active launch/feedback issue;
- only one materially distinct launch experiment may be active at a time;
- stars, visits, downloads, and comments are evidence signals, not automatic product requirements;
- user feedback must pass the promotion gate in `docs/LAUNCH_CONTROL.md` before product scope changes;
- P0/P1 security, cost, download, startup, or integrity regressions pause launch work and are promoted to one scoped engineering issue;
- fake engagement, spam, fabricated evidence, and deceptive claims are prohibited.

## Scope guard

Do not turn FirstWindow into a third coding-agent runtime. Agnes and Hermes remain execution engines; FirstWindow owns beginner onboarding, cost guard, durable state, routing, and acceptance evidence.

New useful ideas that are not required for the active issue belong in a separate issue/backlog item, not the current implementation branch.

Post-release distribution must not become a second product-control plane. `PROJECT_STATE.json` remains canonical and launch evidence only informs promotion decisions.
