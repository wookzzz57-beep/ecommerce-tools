# FirstWindow Project Instructions

## Product contract

FirstWindow is a beginner-first, free-first launcher for coding agents.

The default `$0 Mode` MUST NOT silently invoke a provider whose cost status is unknown.

## Required checks

```bash
python scripts/validate.py
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
- Persist task/checkpoint/evidence under `.firstwindow/tasks/<task_id>/`.
- `$0 Mode` stops instead of falling back to unknown-cost providers.
- Network installer commands are allowlisted to official Agnes/Hermes installer endpoints and require explicit confirmation.
- Do not mutate Agnes or Hermes credentials automatically.
- Do not perform shutdown, restart, sleep, or power operations.
- Prefer Hermes managed Local Models over adding extra local-runtime dependencies for beginners.

## Scope guard

Do not turn FirstWindow into a third coding-agent runtime. Agnes and Hermes remain execution engines; FirstWindow owns beginner onboarding, cost guard, durable state, routing, and acceptance evidence.
