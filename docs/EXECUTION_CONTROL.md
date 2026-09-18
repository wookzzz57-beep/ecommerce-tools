# FirstWindow Execution Control

This document defines how substantial FirstWindow work is planned, executed, paused, resumed, and accepted.

## Canonical control order

Before changing code, read in this order:

1. `AGENTS.md` — project constitution and hard boundaries.
2. `PROJECT_STATE.json` — current phase, active work item, queue, blockers, and resume point.
3. The active GitHub issue — objective, scope, and acceptance criteria.
4. The implementation branch/PR — current evidence and exact diff.

Chat is working context, not canonical project state.

## Preflight gates

Every substantial implementation must pass these gates before code changes:

### G0 — deviation review
Confirm the requested work advances the current FirstWindow objective. If it creates another runtime, weakens the $0 guard, duplicates Agnes/Hermes, or bypasses durable verification, stop or re-scope.

### G1 — sufficiency review
Prefer existing FirstWindow/Agnes/Hermes capability before adding a dependency, service, framework, provider, or control plane.

### G2 — boundary review
Freeze:
- objective,
- in-scope files/components,
- non-goals,
- security/cost boundaries,
- acceptance criteria,
- stop conditions.

### G3 — work-item review
One implementation branch owns one primary engineering issue. Cross-cutting cleanup is allowed only when required by that issue.

### G4 — risk review
Treat changes to cost routing, credentials, installer execution, durable state, verification, release automation, or destructive system behavior as high-risk. Require explicit tests and fresh evidence.

## Execution state machine

Use this progression:

`planned → red → implementing → verifying → ready-to-merge → merged → released`

Use `blocked` from any state when an external dependency or permission prevents safe progress.

A worker saying “done” never skips `verifying`.

## Long-task checkpoint contract

Before stopping, context switching, or handing work to another agent, persist:

- current objective,
- branch and head SHA,
- completed steps,
- fresh evidence,
- blockers,
- exact next action,
- acceptance items still open.

The repository-level pointer is `PROJECT_STATE.json.resume_point`. Runtime task recovery inside user projects remains under `.firstwindow/tasks/<task_id>/`.

## Anti-degradation rules

Stop and reload canonical state when any of these occurs:

- the active objective becomes unclear,
- chat instructions conflict with repository state,
- more than one primary engineering issue is being implemented,
- a new dependency/runtime/provider is proposed without proving necessity,
- acceptance is being inferred from agent prose instead of evidence,
- a failed gate is being ignored to “keep moving,”
- release state and project state disagree.

Do not compensate for context loss by guessing prior decisions.

## Verification ladder

Use the smallest sufficient ladder, escalating with risk:

1. repository/state validation,
2. compile/static checks,
3. unit tests,
4. focused integration or reproducible fixture,
5. Windows package + packaged self-test for distribution changes,
6. release asset/read-back checks for publishing changes,
7. beginner user-flow evidence for UX claims.

Executor output is evidence input, not the final verifier.

## Merge and release gates

A PR is not merge-ready unless:

- scope matches the active issue,
- required checks are green,
- high-risk paths have focused tests,
- acceptance criteria have fresh evidence,
- `PROJECT_STATE.json` has a truthful next resume point,
- no hidden paid fallback or credential handling regression is introduced.

## Scope-change protocol

If new work is useful but not required for the active issue:

1. do not silently add it,
2. record it as an issue or backlog item,
3. keep the current branch focused,
4. promote it only after the current acceptance gate is closed.

This is the primary defense against feature creep and long-task degradation.
