# FirstWindow Project Instructions

## Product contract
FirstWindow is a free-first launcher. Default $0 Mode MUST NOT silently invoke a provider whose cost status is unknown.

## Required checks
```bash
python scripts/validate.py
python -m compileall -q src scripts tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Rules
- Python 3.10+, zero runtime dependencies in v0.1.
- Keep routing policy separate from runtime adapters.
- Never store API keys, tokens, or provider secrets in task state.
- Reject path traversal and unsafe task IDs.
- Worker output is not acceptance evidence.
- Persist task/checkpoint/evidence under `.firstwindow/tasks/<task_id>/`.
- $0 Mode stops rather than falling back to unknown-cost providers.
- Do not mutate Agnes or Hermes global config automatically in v0.1.
