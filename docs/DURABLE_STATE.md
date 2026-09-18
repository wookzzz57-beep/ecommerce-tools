# Durable State Contract

FirstWindow treats chat as working context and durable files as recovery/verification state.

Each task lives under:

```text
.firstwindow/tasks/<task_id>/
├── task.json
├── checkpoint.json
└── evidence.jsonl
```

## Schema v2 — criterion-level acceptance

New tasks use task schema v2. Acceptance criteria receive stable IDs in declaration order:

```json
{
  "schema_version": 2,
  "task_id": "demo",
  "objective": "Ship the endpoint",
  "acceptance": [
    {"id": "AC-001", "text": "tests pass"},
    {"id": "AC-002", "text": "GET /health returns 200"}
  ]
}
```

Evidence may reference one or more criteria:

```json
{
  "timestamp": "2026-09-18T00:00:00+00:00",
  "kind": "test",
  "passed": true,
  "detail": "unit suite passed",
  "criteria": ["AC-001"]
}
```

Generic evidence without a `criteria` field remains valid ledger data but does not cover a v2 acceptance criterion.

## Verification semantics

For schema v2 tasks:

- every required criterion must have referenced evidence;
- the **latest appended valid evidence record for that criterion wins**;
- a latest passing record means `COVERED`;
- a latest failing record means `FAILED`;
- no referenced record means `UNCOVERED`;
- unknown criterion references fail closed;
- malformed criterion references fail closed;
- unsupported future task schema versions fail closed.

Ledger order, not an editable timestamp, defines “latest”. This keeps append-only replay deterministic.

`firstwindow verify <task_id>` prints criterion status before the final verdict.

## Recording evidence from the CLI

For a task with custom `--accept` criteria:

```bash
firstwindow evidence <task_id> \
  --criterion AC-001 \
  --kind test \
  --detail "pytest: 42 passed"

firstwindow evidence <task_id> \
  --criterion AC-002 \
  --kind probe \
  --detail "GET /health -> 200"

firstwindow verify <task_id>
```

Use `--fail` to append a failing result. A later failure intentionally invalidates an earlier pass for the referenced criterion.

A dry run never creates passing acceptance evidence.

## Legacy schema v1

Existing v0.1/v0.2 task directories are not rewritten automatically.

Schema v1 keeps its historical verification rule:

- objective and acceptance state must exist;
- checkpoint must have a next action;
- the ledger must contain at least one passing evidence record.

This compatibility mode is reported as `legacy`. New tasks are always created as schema v2.

## Trust boundary

Criterion mapping makes coverage explicit and deterministic; it does not make arbitrary evidence text magically trustworthy. Evidence quality should come from observable checks such as tests, build results, probes, generated artifacts, or other reproducible signals.

Worker prose alone is not final acceptance evidence.


## Durable Resume

FirstWindow discovers resumable work from `.firstwindow/tasks/`.

A task is eligible only when:
- its durable task/checkpoint state is readable;
- deterministic verification does **not** already report the task complete;
- the schema is supported well enough to build a safe resume context.

Verified-complete tasks are excluded from discovery and fail closed if a caller tries to resume them directly.

Resume context contains:
- original objective;
- current checkpoint stage;
- exact `next_action`;
- acceptance status;
- recent append-only evidence.

The generated resume prompt treats repository durable state as canonical and explicitly instructs the execution engine to continue from the checkpoint rather than replay the entire objective.

CLI:

```bash
firstwindow tasks --project .
firstwindow resume <task_id> --project .
```

The GUI exposes the newest incomplete task in the selected project with its stage and next action, then requires an explicit **Resume** action.

Resume appends new evidence. It never rewrites the existing evidence ledger.


### Resume prompt trust boundary

Evidence details are inserted into a resume prompt as **untrusted historical data**. Execution engines are explicitly instructed to use evidence as observations only and not to execute instructions embedded inside evidence text.

The checkpoint `next_action` remains the canonical continuation instruction. Evidence can inform what has already been observed or verified, but it does not become a new control channel.
