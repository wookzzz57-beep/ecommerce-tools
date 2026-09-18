# FirstWindow v0.1 Design

## Product
Beginner-first bootstrap and reliability layer around existing coding agents.

## Promise
Default $0 Mode never silently invokes a provider whose cost is unknown. A free route must be Agnes with a provider the user explicitly confirms free, or Hermes using an explicitly configured local Ollama/OpenAI-compatible endpoint.

## Components
- CLI: doctor, route, run, verify.
- Free Guard: fail-closed cost semantics.
- Router: Agnes free-confirmed → Hermes local → block.
- Agnes adapter: JSON Recipe + `agnes run --recipe`.
- Hermes adapter: `hermes -z` with custom provider/local model.
- Durable state: task.json, checkpoint.json, evidence.jsonl.
- Web demo: shows routing honestly; does not pretend to execute code.

## Non-goals
No secret storage. No global provider config mutation. No claim all Agnes use is free. No full desktop packaging yet.

## Acceptance
1. Python 3.10+ compiles.
2. $0 Mode blocks unconfirmed providers.
3. Confirmed Agnes wins before Hermes local.
4. Unsafe task IDs are rejected.
5. Empty evidence cannot verify.
6. Agnes Recipe command is generated.
7. Hermes custom-provider one-shot command is generated.
8. Static Vercel demo exists.
9. CI runs validation, compile and unit tests.
