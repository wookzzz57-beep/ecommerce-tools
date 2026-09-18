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

**Hermes Local** is the durable local fallback. Current Hermes Desktop manages its own Local Models runtime and downloads, so FirstWindow v0.2 does not require Ollama as the default beginner path.

Automatic mode:

```text
Agnes Free (confirmed)
        ↓ unavailable
Hermes Managed Local
        ↓ unavailable
BLOCK — no silent paid fallback
```

## Windows beginner preview

GitHub Actions builds a single-file `FirstWindow-Windows-x64.exe`.

Open it and you get:

- **Diagnose** — detect installed runtimes and whether a verified $0 lane is ready
- **Set Up $0 Path** — guided Hermes installation/local-model setup
- **Install Agnes / Hermes** — fixed official installer commands, shown before execution
- **Create Demo** — generate a safe first project
- **Choose Folder**
- **Runtime: Automatic / Agnes Free / Hermes Local**
- **Start Building**
- live run output plus durable task/checkpoint/evidence records

> The v0.2 community EXE is not code-signed yet, so Windows SmartScreen may warn on first launch.

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
firstwindow run "Add a /health endpoint and test it"
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

Chat output is working context. Durable repository state is the recovery source.

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
- remote installers are fixed to documented Agnes/Hermes official commands
- installer execution requires explicit confirmation
- unsafe task IDs/path traversal are rejected
- worker output is not acceptance evidence
- no shutdown, restart, sleep, or power operations

## Verification

Linux CI runs:

```bash
python scripts/validate.py
python -m compileall -q src scripts tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows CI additionally:

- imports Tkinter
- builds the single-file EXE with PyInstaller
- launches the packaged EXE in `--self-test` mode
- prints SHA-256
- uploads the binary artifact
- publishes the first `v0.2.0` release after a successful main build

## Roadmap

- criterion-to-evidence mapping
- resume button for interrupted tasks
- richer progress stream
- signed Windows binaries
- macOS packaged app
- free-quota detection where a provider exposes reliable data
- beginner project templates

MIT licensed.
