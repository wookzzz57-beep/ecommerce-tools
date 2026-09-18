# FirstWindow

> **Your first coding agent. One window. A verified $0 path. No surprise API bill.**

FirstWindow is a beginner-first launcher over **Agnes Code + Hermes Agent**. It hides provider plumbing, keeps a strict $0 guard, persists task/checkpoint/evidence state, and refuses to treat an agent's “done” message as proof by itself.

[Download Windows](../../releases/latest/download/FirstWindow-Windows-x64.exe) · [Beginner Guide](docs/BEGINNER.md)

## The problem

Coding agents are powerful, but the first experience is fragmented:

- install a runtime
- understand providers and API billing
- configure a local model
- open terminals
- recover a half-finished task
- verify whether “done” is actually done

FirstWindow turns that into:

```text
Download → Diagnose → Set Up $0 Path → Choose Folder → Describe Task → Start
```

## Why two runtimes?

**Agnes Free** is the fast cloud lane when you have explicitly verified a free provider.

**Hermes Local** is the durable local fallback. Current Hermes Desktop manages its own Local Models runtime and downloads, so FirstWindow v0.3 does not require Ollama as the default beginner path.

Automatic mode:

```text
Agnes Free (confirmed)
        ↓ unavailable
Hermes Managed Local
        ↓ unavailable
BLOCK — no silent paid fallback
```

## Windows beginner distribution

GitHub Actions builds a single-file `FirstWindow-Windows-x64.exe`.

Open it and you get:

- **Diagnose** — detect installed runtimes and whether a verified $0 lane is ready
- **Set Up $0 Path** — opens the official Hermes Desktop flow when Hermes is missing
- **Get Agnes Desktop / Get Hermes Desktop** — official browser-based beginner install path
- **Advanced CLI fallback** — documented PowerShell installers remain available only by explicit choice
- **Create Demo** — generate a safe first project
- **Choose Folder**
- **Runtime: Automatic / Agnes Free / Hermes Local**
- **Start Building**
- **Resume** — continue the newest incomplete durable task from its checkpoint without replaying completed work
- live run output plus durable task/checkpoint/evidence records

> The v0.3 community EXE is currently unsigned, so Windows SmartScreen may show an unknown-publisher warning. Download `SHA256SUMS.txt` from the same Release to verify the exact packaged EXE.

## Python install

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e .
firstwindow doctor
firstwindow-gui
```

CLI helpers:

```bash
firstwindow setup
firstwindow setup --install hermes --yes
firstwindow demo
firstwindow run "Add a /health endpoint and test it" --accept "tests pass" --accept "GET /health returns 200"
firstwindow tasks --project .
firstwindow resume <task_id> --project .
firstwindow evidence <task_id> --criterion AC-001 --kind test --detail "tests passed"
firstwindow verify <task_id>
```

## Durable state

Each task lives under:

```text
.firstwindow/tasks/<task_id>/
├── task.json
├── checkpoint.json
└── evidence.jsonl
```

New tasks use stable acceptance IDs and criterion-level evidence coverage. Existing v0.1/v0.2 state remains readable without automatic rewriting.

See [Durable State Contract](docs/DURABLE_STATE.md) for schema compatibility and verification semantics.

Chat output is working context. Durable repository state is the recovery source.

### Durable Resume

`firstwindow tasks` lists incomplete tasks only. Verified-complete tasks are excluded and `firstwindow resume` refuses to resume them.

Resume prompts are rebuilt from `task.json`, `checkpoint.json`, and append-only evidence. The checkpoint `next_action` is the primary continuation point; existing passing evidence is included so the agent is instructed not to replay completed work or repeat already-evidenced side effects unless the checkpoint requires it.

## $0 Guard

FirstWindow does **not** claim every Agnes provider is free. Agnes supports free and paid providers. Agnes is eligible for `$0 Mode` only after explicit user confirmation.

For Hermes, FirstWindow reads only the non-secret model configuration:

```text
hermes config get model --json
```

A managed `llamacpp` Local Model is treated as a local lane. FirstWindow does not read Hermes credential files.

## Security boundaries

- no API keys stored by FirstWindow
- no automatic paid fallback
- beginner setup opens official Desktop download pages instead of silently executing remote scripts
- advanced CLI installers remain fixed to documented Agnes/Hermes commands and require explicit confirmation
- unsafe task IDs/path traversal are rejected
- worker output is not acceptance evidence
- no shutdown, restart, sleep, or power operations

## Contributor control plane

Substantial work starts from:

1. `AGENTS.md` — hard project boundaries.
2. `PROJECT_STATE.json` — current phase, active issue, queue, blockers, and resume point.
3. `docs/EXECUTION_CONTROL.md` — preflight, long-task, anti-drift, and acceptance gates.
4. the active GitHub issue — implementation scope and acceptance criteria.

One primary engineering issue is allowed per implementation branch.

## Verification

Linux CI runs:

```bash
python scripts/check_project_state.py
python scripts/validate.py
python -m compileall -q src scripts tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows CI additionally:

- imports Tkinter
- builds the single-file EXE with PyInstaller
- launches the packaged EXE in `--self-test` mode
- generates `SHA256SUMS.txt`
- uploads the EXE + checksum as CI artifacts
- publishes a Release only from a `v*` tag whose version matches `pyproject.toml`

## Roadmap

- richer progress stream
- code-signed Windows binaries
- macOS packaged app
- free-quota detection where a provider exposes reliable data
- beginner project templates

MIT licensed.
