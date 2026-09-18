# FirstWindow

> **Your first coding agent. A verified $0 path, one window, no surprise API bill.**

FirstWindow is a beginner-friendly launcher that routes coding work to an explicitly confirmed free Agnes setup or a local Hermes + Ollama setup, while keeping durable task state, checkpoints, and evidence on disk.

## The promise

**$0 Mode never silently falls back to a provider whose cost is unknown.**

## Architecture

```text
FirstWindow
├─ Beginner CLI / web demo
├─ $0 Free Guard
├─ Router
│  ├─ Agnes free-confirmed lane
│  └─ Hermes + Ollama local lane
└─ Durable Core
   ├─ task.json
   ├─ checkpoint.json
   └─ evidence.jsonl
```

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
firstwindow doctor
```

For an Agnes provider you have verified is free:

```bash
export FIRSTWINDOW_AGNES_FREE_CONFIRMED=1
```

For Hermes + local Ollama, configure Hermes Custom endpoint to `http://localhost:11434/v1`, then:

```bash
export FIRSTWINDOW_HERMES_LOCAL_CONFIRMED=1
export FIRSTWINDOW_LOCAL_MODEL="qwen3.5:9b"
```

Dry run:

```bash
firstwindow run "Add a /health endpoint and test it" --dry-run
```

## Ships in v0.1

- deterministic Free Guard
- Agnes Recipe adapter using `agnes run --recipe`
- Hermes one-shot adapter using `hermes -z`
- durable task/checkpoint/evidence state
- verification gate
- zero-dependency Python CLI
- tests + GitHub Actions
- static public router demo

## Scope honesty

FirstWindow does not claim every Agnes provider is free. The free guard requires explicit confirmation. The Hermes local lane requires an already configured local endpoint in v0.1 and does not rewrite global Hermes settings.

MIT licensed.
